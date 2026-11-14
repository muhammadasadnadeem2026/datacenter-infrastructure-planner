"""Tabular views of a full calculation, shared by the XLSX, CSV and PDF exporters.

These functions only reshape engine output; they never compute engineering values.
"""

from __future__ import annotations

from typing import Any

MODULE_TITLES = {
    "it": "IT Load",
    "rack_count": "Rack Capacity",
    "space": "Space / White Space",
    "circuit": "Branch Circuits",
    "pdu": "Rack PDU",
    "ups": "UPS",
    "battery": "UPS Battery",
    "facility": "Facility / PUE",
    "environment": "Environment",
    "cooling": "Cooling",
    "utility": "Utility",
    "transformer": "Transformer",
    "generator": "Generator",
    "bess": "BESS",
    "energy": "Energy & Cost",
}


def display(value: Any) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        a = abs(value)
        if a >= 100:
            return f"{value:,.0f}"
        if a >= 1:
            return f"{value:,.2f}"
        if a == 0:
            return "0"
        return f"{value:.4g}"
    return "" if value is None else str(value)


def flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            rows += flatten(v, f"{prefix}.{k}" if prefix else k)
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
        rows.append((prefix, f"[{len(obj)} items]"))
    else:
        rows.append((prefix, obj))
    return rows


def sheets(inputs: dict[str, Any], result: dict[str, Any]) -> dict[str, tuple[list[str], list[list[Any]]]]:
    modules = result["modules"]
    out: dict[str, tuple[list[str], list[list[Any]]]] = {}
    out["Inputs"] = (["Field", "Value"], [[k, v] for k, v in flatten(inputs)])
    out["Results"] = (
        ["Module", "Key", "Result", "Value", "Unit"],
        [[MODULE_TITLES.get(m, m), s["key"], s["label"], s["value"], s["unit"]]
         for m, mod in modules.items() for s in mod["steps"]],
    )
    it_data = modules["it"]["data"]
    out["Device Load List"] = (
        ["Type", "Description", "Qty", "Nameplate W", "Utilization %", "Calculated W", "Rack"],
        [[d["equipment_type"], d["description"], d["quantity"], d["nameplate_w"], d["utilization_pct"],
          d["calculated_w"], d["rack"]] for d in it_data.get("devices", [])],
    )
    if it_data.get("rack_summary"):
        rack_rows = [[r["rack"], r["devices"], r["kw"]] for r in it_data["rack_summary"]]
    else:
        it_steps = {s["key"]: s["value"] for s in modules["it"]["steps"]}
        rack_rows = [[f"Average rack (× {it_steps['rack_count']})", "", it_steps["kw_per_rack"]]]
    out["Rack Summary"] = (["Rack", "Devices", "kW"], rack_rows)
    out["Capacity Balance"] = (
        ["System", "Required", "Installed", "Usable", "Unit", "Loading %", "Reserve", "Redundancy",
         "Max IT kW", "Status"],
        [[r["label"], r["required"], r["installed"], r["usable"], r["unit"], r["loading_pct"], r["reserve"],
          r["redundancy"], r["max_it_kw"], r["status"]] for r in result["capacity"]["rows"]],
    )
    out["Warnings"] = (
        ["Severity", "Code", "Title", "Message", "System", "Reference"],
        [[w["severity"], w["code"], w["title"], w["message"], w["affected_system"], w["reference"]]
         for w in result["warnings"]],
    )
    out["Calculations"] = (
        ["Module", "Result", "Formula", "Calculation", "Value", "Unit", "Assumption", "Reference"],
        [[MODULE_TITLES.get(m, m), s["label"], s["formula"], s["substitution"], s["value"], s["unit"],
          s["assumption"], s["reference"]] for m, mod in modules.items() for s in mod["steps"]],
    )
    return out
