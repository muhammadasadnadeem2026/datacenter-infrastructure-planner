import copy

import pytest
from pydantic import ValidationError

from app.calculations.full import run_full_calculation
from app.constants.presets import PRESET_META, get_preset
from app.schemas.inputs import ProjectInputs
from app.version import CALC_ENGINE_VERSION


def run(d):
    return run_full_calculation(ProjectInputs.model_validate(d))


def test_acceptance_example(acceptance_inputs):
    r = run(acceptance_inputs)
    m = r.modules
    assert m["it"].v("it_kw") == 60
    assert m["it"].v("it_kva") == pytest.approx(63.16, abs=0.005)
    assert m["cooling"].v("btu_hr") == pytest.approx(204_729, abs=1)
    assert m["cooling"].v("tons") == pytest.approx(17.06, abs=0.005)
    assert m["facility"].v("facility_kw") == 90
    assert m["energy"].v("annual_facility_kwh") == pytest.approx(788_400)
    assert m["energy"].v("annual_cost") == pytest.approx(102_492, abs=1)
    # every displayed number carries its derivation
    for mod in m.values():
        for step in mod.steps.values():
            assert step.formula, f"{mod.module}.{step.key} lacks a formula"
            assert step.substitution != "", f"{mod.module}.{step.key} lacks a substitution"


def test_result_records_engine_version(acceptance_inputs):
    d = run(acceptance_inputs).to_dict()
    assert d["engine_version"] == CALC_ENGINE_VERSION


@pytest.mark.parametrize("preset", [p["id"] for p in PRESET_META])
@pytest.mark.parametrize("mode", ["quick", "standard", "engineering"])
def test_every_preset_every_mode(preset, mode):
    d = {**get_preset(preset), "mode": mode}
    out = run(d).to_dict()
    assert out["modules"]["it"]["steps"]
    assert out["capacity"]["rows"]


def test_modes_gate_modules():
    base = get_preset("colocation")
    quick = run({**base, "mode": "quick"}).modules
    std = run({**base, "mode": "standard"}).modules
    eng = run({**base, "mode": "engineering"}).modules
    assert "ups" not in quick and "circuit" not in quick
    assert {"ups", "circuit", "pdu", "space"} <= std.keys()
    assert "transformer" not in std and "generator" not in std
    assert {"transformer", "generator", "environment", "utility"} <= eng.keys()


def test_propagation_rack_power_to_everything():
    a = get_preset("enterprise")
    a["mode"] = "engineering"
    b = copy.deepcopy(a)
    b["it"]["kw_per_rack"] = 11 * 2
    b["rack"]["rack_rating_kw"] = 24
    ra, rb = run(a).modules, run(b).modules
    for mod, key in [("it", "it_kva"), ("circuit", "rack_kva"), ("ups", "installed_kva"),
                     ("transformer", "required_kva"), ("facility", "facility_kw"),
                     ("generator", "critical_load_kw"), ("cooling", "btu_hr"), ("energy", "annual_facility_kwh")]:
        assert rb[mod].v(key) == pytest.approx(2 * ra[mod].v(key)), f"{mod}.{key} did not propagate"


def test_bottleneck_accounts_for_power_factor():
    d = get_preset("enterprise")
    d["mode"] = "engineering"
    d["it"].update(rack_count=100, kw_per_rack=84)  # 8.4 MW IT
    d["rack"]["rack_rating_kw"] = 100
    d["facility"]["pue"] = 1.0
    d["ups"].update(module_kva=0, target_load_pct=80, redundancy="N", modules_n=10)  # 10 MVA-class UPS
    d["transformer"].update(kva_rating=4500, quantity=2, redundancy="N")  # 9 MVA
    d["utility"]["service_capacity_kva"] = 20000
    d["generator"].update(unit_kw=3000, unit_kva=3750, quantity=4, redundancy="N")  # 12 MW
    d["cooling"].update(unit_capacity_kw=950, unit_count=10, redundancy="N")  # 9.5 MW thermal
    r = run(d)
    # 8.4 MW at PF 0.95 = 8.84 MVA -> 98 % of a 9 MVA transformer bank; cooling is 88 %.
    b = r.capacity["bottleneck"]
    assert b["system"] == "transformer"
    assert b["loading_pct"] == pytest.approx(8400 / 0.95 / 9000 * 100)


def test_generator_load_basis_options():
    d = get_preset("enterprise")
    d["mode"] = "engineering"
    for basis, expected in [("it_only", 220), ("full", 330)]:
        d["generator"]["load_basis"] = basis
        assert run(d).modules["generator"].v("critical_load_kw") == pytest.approx(expected)
    d["generator"].update(load_basis="it_cooling")
    d["facility"].update(cooling_share_pct=70)
    assert run(d).modules["generator"].v("critical_load_kw") == pytest.approx(220 + 110 * 0.7)
    d["generator"].update(load_basis="custom", custom_load_kw=123)
    assert run(d).modules["generator"].v("critical_load_kw") == 123


def test_sankey_labels_overhead_without_split(acceptance_inputs):
    s = run(acceptance_inputs).sankey
    names = [n["name"] for n in s["nodes"]]
    assert names == ["Utility power", "IT load", "Facility Overhead"]
    assert sum(link["value"] for link in s["links"]) == pytest.approx(90)


def test_power_flow_visibility():
    d = get_preset("server_closet")
    flow = run(d).power_flow
    vis = {n["id"]: n["visible"] for n in flow["nodes"]}
    assert vis["transformer"] is False
    assert not any(s["visible"] for s in flow["sources"])
    ai = run(get_preset("ai_cluster")).power_flow
    assert {s["id"]: s["visible"] for s in ai["sources"]} == {"generator": True, "bess": True}


def test_warnings_structure_and_liquid():
    out = run(get_preset("ai_cluster")).to_dict()
    codes = {w["code"] for w in out["warnings"]}
    assert "LIQUID_COOLING_REQUIRED" in codes
    for w in out["warnings"]:
        assert set(w) == {"severity", "code", "title", "message", "affected_system", "reference"}
        assert w["severity"] in {"info", "caution", "critical"}


def test_warning_rules_fire():
    d = get_preset("enterprise")
    d["mode"] = "engineering"
    d["it"]["power_factor"] = 0.85
    d["facility"]["pue"] = 1.02
    d["transformer"].update(kva_rating=200)
    d["generator"].update(unit_kw=100, unit_kva=125)
    d["environment"].update(altitude=2000, ambient_temp=38)
    d["electrical"].update(receptacle_id="custom", voltage=208, current=30, phase="single", circuits_per_rack=1)
    codes = {w["code"] for w in run(d).warnings}
    assert {"LOW_POWER_FACTOR", "PUE_UNREALISTIC", "TRANSFORMER_OVERLOAD", "GENERATOR_INSUFFICIENT",
            "ALTITUDE_DERATE", "TEMP_OUTSIDE_ALLOWABLE", "CIRCUIT_OVERLOAD"} <= codes


def test_very_large_ai_deployment():
    d = get_preset("ai_cluster")
    d["it"].update(rack_count=2000, kw_per_rack=150)  # 300 MW IT
    d["rack"]["rack_rating_kw"] = 150
    d["bess"].update(container_power_mw=5, container_energy_mwh=10)
    r = run(d)
    assert r.modules["it"].v("it_mw") == 300
    assert r.modules["bess"].v("required_mw") == pytest.approx(375)
    assert r.modules["bess"].v("containers_total") >= 75


def test_receptacle_library_overrides_custom_fields():
    d = get_preset("enterprise")
    d["electrical"].update(receptacle_id="nema_l6_30", voltage=999, current=999, phase="three")
    c = run(d).modules["circuit"]
    assert c.v("nominal_kva") == pytest.approx(6.24)


# ---------------------------------------------------------------- validation


@pytest.mark.parametrize("path,value", [
    (("it", "rack_count"), 0),
    (("it", "kw_per_rack"), 0),
    (("it", "kw_per_rack"), -5),
    (("it", "power_factor"), 0),
    (("it", "power_factor"), 1.2),
    (("facility", "pue"), 0.99),
    (("financial", "electricity_rate"), -0.1),
    (("space", "room_area"), 0),
    (("ups", "target_load_pct"), 0),
    (("ups", "target_load_pct"), 101),
    (("transformer", "efficiency"), 0),
    (("transformer", "efficiency"), 1.1),
    (("electrical", "voltage"), 0),
    (("electrical", "current"), -1),
])
def test_invalid_inputs_rejected(path, value):
    d = get_preset("enterprise")
    d[path[0]][path[1]] = value
    with pytest.raises(ValidationError):
        ProjectInputs.model_validate(d)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_nan_infinity_rejected(bad):
    d = get_preset("enterprise")
    d["it"]["kw_per_rack"] = bad
    with pytest.raises(ValidationError):
        ProjectInputs.model_validate(d)


def test_redundancy_quantity_consistency():
    d = get_preset("enterprise")
    d["transformer"].update(quantity=1, redundancy="N+1")
    with pytest.raises(ValidationError):
        ProjectInputs.model_validate(d)
    d["transformer"].update(quantity=3, redundancy="2N")
    with pytest.raises(ValidationError):
        ProjectInputs.model_validate(d)


def test_overhead_shares_cannot_exceed_100():
    d = get_preset("enterprise")
    d["facility"].update(cooling_share_pct=70, electrical_loss_share_pct=40)
    with pytest.raises(ValidationError):
        ProjectInputs.model_validate(d)


def test_unknown_fields_rejected():
    d = get_preset("enterprise")
    d["it"]["surprise"] = 1
    with pytest.raises(ValidationError):
        ProjectInputs.model_validate(d)
