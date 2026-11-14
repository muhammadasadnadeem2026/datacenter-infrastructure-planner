"""Infrastructure capacity balance and bottleneck detection.

Each row compares like with like (kW with kW, kVA with kVA, kW-thermal with
kW-thermal), so power factor is accounted for inside every row. Rows are then ranked
by loading %, and by the maximum IT load each system could support if the IT load
scaled linearly, which gives a unit-independent bottleneck.
"""

from __future__ import annotations

from typing import Any

from app.calculations.trace import ModuleResult, cmp_round
from app.constants.thresholds import CAPACITY_CAUTION_PCT, CAPACITY_CRITICAL_PCT

SYSTEM_LABELS = {
    "it": "IT (rack power)",
    "ups": "UPS",
    "transformer": "Transformer",
    "utility": "Utility service",
    "generator": "Generator",
    "bess_power": "BESS power",
    "bess_energy": "BESS energy",
    "cooling": "Cooling",
}


def capacity_status(loading_pct: float) -> str:
    val = cmp_round(loading_pct)
    if val > CAPACITY_CRITICAL_PCT:
        return "critical"
    if val > CAPACITY_CAUTION_PCT:
        return "caution"
    return "ok"


def make_row(
    system: str,
    *,
    required: float | None,
    installed: float | None,
    usable: float | None,
    unit: str,
    redundancy: str,
    it_kw: float,
    power_factor: float | None = None,
    note: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "system": system,
        "label": SYSTEM_LABELS[system],
        "required": required,
        "installed": installed,
        "usable": usable,
        "unit": unit,
        "redundancy": redundancy,
        "loading_pct": None,
        "reserve": None,
        "max_it_kw": None,
        "usable_kw_equivalent": None,
        "status": "not_configured",
        "note": note,
    }
    if required is None or usable is None or usable <= 0 or required <= 0:
        return row
    loading = required / usable * 100
    row.update(
        loading_pct=loading,
        reserve=usable - required,
        max_it_kw=it_kw * usable / required,
        status=capacity_status(loading),
    )
    if unit == "kVA" and power_factor:
        row["usable_kw_equivalent"] = usable * power_factor
    return row


def build_capacity_balance(
    *,
    it_kw: float,
    modules: dict[str, ModuleResult],
    rack_capacity_kw: float,
    facility_pf: float,
    it_pf: float,
    utility_capacity_kva: float,
) -> dict[str, Any]:
    rows = [
        make_row("it", required=it_kw, installed=rack_capacity_kw, usable=rack_capacity_kw, unit="kW",
                 redundancy="—", it_kw=it_kw, note="Design IT load vs provisioned rack power."),
    ]
    ups = modules.get("ups")
    rows.append(make_row(
        "ups",
        required=ups.v("load_kva") if ups else None,
        installed=ups.v("installed_kva") if ups else None,
        usable=ups.v("usable_kva") if ups else None,
        unit="kVA", redundancy=ups.data["redundancy"] if ups else "—", it_kw=it_kw, power_factor=it_pf,
    ))
    tx = modules.get("transformer")
    rows.append(make_row(
        "transformer",
        required=tx.v("required_kva") if tx else None,
        installed=tx.v("installed_kva") if tx else None,
        usable=tx.v("usable_kva") if tx else None,
        unit="kVA", redundancy=tx.data["redundancy"] if tx else "—", it_kw=it_kw, power_factor=facility_pf,
    ))
    fac = modules["facility"]
    utility_required = tx.v("input_kva") if tx else fac.v("facility_kva")
    has_utility = "utility" in modules and utility_capacity_kva > 0
    rows.append(make_row(
        "utility",
        required=utility_required if has_utility else None,
        installed=utility_capacity_kva if has_utility else None,
        usable=utility_capacity_kva if has_utility else None,
        unit="kVA", redundancy="—", it_kw=it_kw, power_factor=facility_pf,
        note="Includes transformer losses." if tx else "",
    ))
    gen = modules.get("generator")
    rows.append(make_row(
        "generator",
        required=gen.v("critical_load_kw") if gen else None,
        installed=gen.v("installed_kw") if gen else None,
        usable=gen.v("usable_kw") if gen else None,
        unit="kW", redundancy=gen.data["redundancy"] if gen else "—", it_kw=it_kw,
        note=f"Load basis: {gen.data['load_basis']}" if gen else "",
    ))
    bess = modules.get("bess")
    rows.append(make_row(
        "bess_power",
        required=bess.v("required_mw") if bess else None,
        installed=bess.v("installed_mw") if bess else None,
        usable=bess.v("usable_mw") if bess else None,
        unit="MW", redundancy=bess.data["redundancy"] if bess else "—", it_kw=it_kw,
    ))
    rows.append(make_row(
        "bess_energy",
        required=bess.v("battery_mwh") if bess else None,
        installed=bess.v("installed_mwh") if bess else None,
        usable=bess.v("installed_mwh") if bess else None,
        unit="MWh", redundancy=bess.data["redundancy"] if bess else "—", it_kw=it_kw,
        note="Nameplate (BOL) energy vs required nameplate energy." if bess else "",
    ))
    cool = modules.get("cooling")
    has_cool = cool is not None and "usable_kw" in cool.steps
    rows.append(make_row(
        "cooling",
        required=cool.v("total_heat_kw") if has_cool else None,
        installed=cool.v("installed_kw") if has_cool else None,
        usable=cool.v("usable_kw") if has_cool else None,
        unit="kW thermal", redundancy=cool.data.get("redundancy", "—") if has_cool else "—", it_kw=it_kw,
    ))

    configured = [r for r in rows if r["loading_pct"] is not None]
    bottleneck = None
    if configured:
        worst = max(configured, key=lambda r: r["loading_pct"])
        bottleneck = {
            "system": worst["system"],
            "label": worst["label"],
            "loading_pct": worst["loading_pct"],
            "max_it_kw": worst["max_it_kw"],
            "status": worst["status"],
            "message": (
                f"{worst['label']} is the limiting system at {worst['loading_pct']:.1f} % of usable capacity; "
                f"it could support about {worst['max_it_kw']:,.0f} kW of IT load at the current ratios."
            ),
        }
    return {"rows": rows, "bottleneck": bottleneck}
