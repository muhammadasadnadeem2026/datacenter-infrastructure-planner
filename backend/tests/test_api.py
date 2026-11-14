"""Integration tests through the HTTP API."""

import io

import pytest
from openpyxl import load_workbook

from app.constants.presets import get_preset


def steps(body, module):
    return {s["key"]: s["value"] for s in body["modules"][module]["steps"]}


def test_health_and_meta(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    meta = client.get("/api/meta").json()
    assert meta["engine_version"]
    assert "qualified engineering professionals" in meta["disclaimer"]


def test_openapi_available(client):
    spec = client.get("/openapi.json").json()
    assert "/api/calculate/full" in spec["paths"]


def test_full_acceptance(client, acceptance_inputs):
    r = client.post("/api/calculate/full", json=acceptance_inputs)
    assert r.status_code == 200
    body = r.json()
    assert steps(body, "it")["it_kw"] == 60
    assert steps(body, "energy")["annual_cost"] == pytest.approx(102_492)
    assert body["summary"]


def test_full_rejects_invalid(client):
    d = get_preset("enterprise")
    d["it"]["power_factor"] = 0
    r = client.post("/api/calculate/full", json=d)
    assert r.status_code == 422


@pytest.mark.parametrize("path,payload,module,key,expected", [
    ("cooling", {"it_kw": 60, "rack_count": 10}, "cooling", "tons", 17.0607),
    ("circuit", {"voltage": 208, "current": 30, "phase": "single", "rack_kw": 11, "power_factor": 0.95},
     "circuit", "min_circuits", 3),
    ("power-factor", {"kw": 60, "power_factor": 0.95}, "power_factor", "kva", 63.1579),
    ("convert", {"conversion": "amps_to_kva", "value": 400, "voltage": 480, "phase": "three"},
     "convert", "result", 332.55),
    ("rack-count", {"it_kw": 8400, "rack_power_kw": 142}, "rack_count", "racks_required", 60),
    ("rack-density", {"rack_count": 10, "kw_per_rack": 6, "room_area": 1000}, "space", "w_per_ft2", 60),
    ("ups", {"load_kw": 60, "power_factor": 0.95, "ups": {"redundancy": "2N", "modules_n": 1,
                                                           "target_load_pct": 100}},
     "ups", "installed_kva", 126.3158),
    ("pdu", {"rack_kw": 11, "pdu": {"voltage": 208, "amperage": 30, "phase": "three", "feed": "ab"}},
     "pdu", "pdus_total", 4),
    ("transformer", {"required_kw": 1900, "power_factor": 0.95,
                     "transformer": {"kva_rating": 2500, "quantity": 2, "redundancy": "N+1"}},
     "transformer", "loading_pct", 80),
    ("generator", {"load_kw": 3000, "generator": {"unit_kw": 2000, "unit_kva": 2500, "quantity": 3}},
     "generator", "usable_kw", 4000),
    ("bess", {"power_mw": 10, "bess": {"duration_min": 15, "container_power_mw": 2.5}}, "bess",
     "containers_power", 4),
])
def test_tool_endpoints(client, path, payload, module, key, expected):
    r = client.post(f"/api/calculate/{path}", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert steps(body, module)[key] == pytest.approx(expected, abs=1e-2)
    assert isinstance(body["warnings"], list)


def test_it_load_device_mode(client):
    payload = {"it": {"input_mode": "device_list", "rack_count": 1, "kw_per_rack": 1, "power_factor": 0.95,
                      "devices": [{"quantity": 2, "nameplate_w": 1000, "utilization_pct": 50}]}}
    body = client.post("/api/calculate/it-load", json=payload).json()
    assert steps(body, "it")["it_kw"] == 1.0


def test_ai_rack(client):
    payload = {
        "rack_count": 8, "rack_power_kw": 120, "pue": 1.25, "room_area": 1200,
        "electrical": {"receptacle_id": "iec_60309_63a_415", "voltage": 415, "current": 63, "phase": "three"},
        "pdu": {"voltage": 415, "amperage": 63, "phase": "three"},
    }
    body = client.post("/api/calculate/ai-rack", json=payload).json()
    assert steps(body, "it")["it_kw"] == 960
    assert steps(body, "facility")["facility_kw"] == 1200
    assert any(w["code"] == "LIQUID_COOLING_REQUIRED" for w in body["warnings"])


def test_constants(client):
    rec = client.get("/api/constants/receptacles").json()
    l630 = next(r for r in rec if r["id"] == "nema_l6_30")
    assert l630["nominal_kva"] == pytest.approx(6.24)
    assert l630["usable_kva"] == pytest.approx(4.992)
    assert client.get("/api/constants/cooling-classes").json()["cooling_classes"][-1]["id"] == "liquid"
    assert any(v["voltage_v"] == 34500 for v in client.get("/api/constants/voltage-levels").json())
    presets = client.get("/api/constants/presets").json()
    assert {p["id"] for p in presets} >= {"server_closet", "ai_cluster", "custom"}
    refs = client.get("/api/constants/references").json()
    assert all({"id", "organization", "document", "edition", "section", "description", "url",
                "date_verified"} <= set(r) for r in refs)


def test_project_crud_and_versioning(client, acceptance_inputs):
    r = client.post("/api/projects", json={"name": "Hall A", "inputs": acceptance_inputs})
    assert r.status_code == 201
    p = r.json()
    pid = p["id"]
    assert p["calculator_version"]
    assert p["results"]["modules"]["it"]["steps"][0]["value"] == 60
    assert isinstance(p["warnings"], list)

    assert client.get(f"/api/projects/{pid}").json()["name"] == "Hall A"
    assert len(client.get("/api/projects").json()) == 1

    upd = client.put(f"/api/projects/{pid}", json={"name": "Hall A rev B"}).json()
    assert upd["name"] == "Hall A rev B"

    new_inputs = {**acceptance_inputs, "it": {**acceptance_inputs["it"], "rack_count": 20}}
    upd = client.put(f"/api/projects/{pid}", json={"inputs": new_inputs}).json()
    assert steps(upd["results"], "it")["it_kw"] == 120

    clone = client.post(f"/api/projects/{pid}/clone").json()
    assert clone["id"] != pid and clone["name"].endswith("(copy)")

    assert client.post(f"/api/projects/{pid}/recalculate").status_code == 200
    assert client.delete(f"/api/projects/{pid}").status_code == 204
    assert client.get(f"/api/projects/{pid}").status_code == 404


def test_project_rejects_invalid_inputs(client):
    d = get_preset("enterprise")
    d["facility"]["pue"] = 0.5
    assert client.post("/api/projects", json={"name": "x", "inputs": d}).status_code == 422


def test_exports(client, acceptance_inputs):
    body = {"project_name": "Hall A", "inputs": acceptance_inputs}
    pdf = client.post("/api/export/pdf", json=body)
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
    xlsx = client.post("/api/export/xlsx", json=body)
    wb = load_workbook(io.BytesIO(xlsx.content))
    assert {"Inputs", "Results", "Device Load List", "Rack Summary", "Capacity Balance", "Warnings",
            "Calculations"} <= set(wb.sheetnames)
    csv = client.post("/api/export/csv/calculations", json=body)
    assert csv.status_code == 200
    assert "kVA = kW / PF" in csv.text
    assert client.post("/api/export/csv/bogus", json=body).status_code == 422


def test_engineering_mode_pdf(client):
    body = {"project_name": "AI hall", "inputs": get_preset("ai_cluster")}
    assert client.post("/api/export/pdf", json=body).content[:4] == b"%PDF"
