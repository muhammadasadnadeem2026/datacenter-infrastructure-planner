"""Power-flow (single-line-style) and energy Sankey data built from computed modules.

No new formulas here: every value is read from a ModuleResult step.
"""

from __future__ import annotations

from typing import Any

from app.calculations.trace import ModuleResult


def _metric(label: str, value: Any, unit: str) -> dict[str, Any]:
    return {"label": label, "value": value, "unit": unit}


def _row(balance: dict[str, Any], system: str) -> dict[str, Any] | None:
    return next((r for r in balance["rows"] if r["system"] == system), None)


def build_power_flow(
    modules: dict[str, ModuleResult],
    balance: dict[str, Any],
    *,
    utility_voltage: float,
) -> dict[str, Any]:
    it = modules["it"]
    fac = modules["facility"]
    tx = modules.get("transformer")
    ups = modules.get("ups")
    pdu = modules.get("pdu")
    gen = modules.get("generator")
    bess = modules.get("bess")
    util_row = _row(balance, "utility")

    nodes: list[dict[str, Any]] = []
    upstream_kva = tx.v("input_kva") if tx else fac.v("facility_kva")
    nodes.append({
        "id": "utility", "label": "Utility", "visible": True,
        "metrics": [
            _metric("Demand", upstream_kva / 1000, "MVA"),
            _metric("Voltage", (tx.data["primary_voltage"] if tx else utility_voltage) / 1000, "kV"),
            *([_metric("Loading", util_row["loading_pct"], "%")] if util_row and util_row["loading_pct"] else []),
        ],
    })
    nodes.append({
        "id": "mv_switchgear", "label": "MV Switchgear", "visible": tx is not None,
        "metrics": [_metric("Voltage", tx.data["primary_voltage"] / 1000, "kV")] if tx else [],
    })
    nodes.append({
        "id": "transformer", "label": "Transformer", "visible": tx is not None,
        "metrics": [
            _metric("Installed", tx.v("installed_kva") / 1000, "MVA"),
            _metric("Loading", tx.get("loading_pct"), "%"),
            _metric("Fault (approx.)", tx.v("fault_current_ka"), "kA"),
        ] if tx else [],
    })
    nodes.append({
        "id": "lv_switchgear", "label": "LV Switchgear", "visible": True,
        "metrics": [
            _metric("Facility", fac.v("facility_mw"), "MW"),
            _metric("Facility", fac.v("facility_kva") / 1000, "MVA"),
            *([_metric("Voltage", tx.data["secondary_voltage"], "V")] if tx else []),
        ],
    })
    nodes.append({
        "id": "ups", "label": "UPS", "visible": ups is not None,
        "metrics": [
            _metric("Installed", ups.v("installed_kva"), "kVA"),
            _metric("Loading (N)", ups.v("utilization_usable_pct"), "%"),
            _metric("Modules", ups.v("module_count"), ""),
        ] if ups else [],
    })
    nodes.append({
        "id": "pdu", "label": "Rack PDU", "visible": pdu is not None,
        "metrics": [
            _metric("Per rack", pdu.v("pdus_total"), "PDUs"),
            _metric("Loading", pdu.v("loading_pct"), "%"),
        ] if pdu else [],
    })
    nodes.append({
        "id": "rack", "label": "IT Racks", "visible": True,
        "metrics": [
            _metric("IT load", it.v("it_mw"), "MW"),
            _metric("Racks", it.v("rack_count"), ""),
            _metric("Per rack", it.v("kw_per_rack"), "kW"),
        ],
    })
    sources = [
        {
            "id": "generator", "label": "Generator", "visible": gen is not None, "feeds": "lv_switchgear",
            "metrics": [
                _metric("Usable", gen.v("usable_kw") / 1000, "MW"),
                _metric("Loading", gen.get("loading_pct"), "%"),
            ] if gen else [],
        },
        {
            "id": "bess", "label": "BESS", "visible": bess is not None, "feeds": "lv_switchgear",
            "metrics": [
                _metric("Power", bess.v("installed_mw"), "MW"),
                _metric("Energy", bess.v("installed_mwh"), "MWh"),
            ] if bess else [],
        },
    ]
    return {"nodes": nodes, "sources": sources}


def build_sankey(fac: ModuleResult) -> dict[str, Any]:
    breakdown = fac.data["breakdown"]
    nodes = [{"name": "Utility power"}] + [{"name": b["label"]} for b in breakdown]
    links = [{"source": 0, "target": i + 1, "value": b["kw"]} for i, b in enumerate(breakdown) if b["kw"] > 0]
    return {"nodes": nodes, "links": links, "split_given": fac.data["split_given"]}
