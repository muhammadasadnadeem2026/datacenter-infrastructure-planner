"""Standby generator sizing and capacity check."""

from __future__ import annotations

from app.calculations import electrical
from app.calculations.redundancy import installed_unit_count, units_needed, usable_units
from app.calculations.trace import ModuleResult, fmt

LOAD_BASIS_LABELS = {
    "it_only": "Critical IT only",
    "it_cooling": "IT + cooling",
    "full": "Full facility",
    "custom": "Custom essential load",
}


def unit_usable_kw(unit_kw: float, unit_kva: float, power_factor: float) -> float:
    """A generator is limited by the lower of its kW rating and its kVA rating at the load PF."""
    return min(unit_kw, electrical.kw_from_kva(unit_kva, power_factor))


def compute_generator(
    *,
    critical_load_kw: float,
    load_basis: str,
    load_basis_note: str = "",
    unit_kw: float,
    unit_kva: float,
    power_factor: float,
    quantity: int,
    redundancy: str,
    step_load_pct: float,
    target_loading_pct: float,
    derate_factor: float = 1.0,
) -> ModuleResult:
    r = ModuleResult("generator")
    r.data["redundancy"] = redundancy
    r.data["load_basis"] = load_basis
    load = r.add("critical_load_kw", "Generator-backed load", critical_load_kw, "kW",
                 LOAD_BASIS_LABELS.get(load_basis, load_basis), fmt(critical_load_kw),
                 assumption=load_basis_note or "Load basis selected by user.")
    r.add("critical_load_kva", "Generator-backed load", electrical.kva_from_kw(load, power_factor), "kVA",
          "kVA = kW / PF", f"{fmt(load)} / {fmt(power_factor)}")
    per_unit_raw = unit_usable_kw(unit_kw, unit_kva, power_factor)
    per_unit = r.add("unit_usable_kw", "Usable rating per generator", per_unit_raw * derate_factor, "kW",
                     "min(kW rating, kVA × PF) × site derate",
                     f"min({fmt(unit_kw)}, {fmt(unit_kva)} × {fmt(power_factor)}) × {fmt(derate_factor)}",
                     assumption="Site derate factor from Environment module (manufacturer data).",
                     reference="manufacturer-data")
    target = target_loading_pct / 100
    required_cap = r.add("required_capacity_kw", "Required generator capacity", load / target, "kW",
                         "Required = Load kW / target loading", f"{fmt(load)} / {fmt(target)}")
    n_run = r.add("units_required_n", "Generators needed to carry load (n)", units_needed(required_cap, per_unit),
                  "units", "n = ceil(Required kW / unit kW)", f"ceil({fmt(required_cap)} / {fmt(per_unit)})")
    r.add("units_recommended", f"Generators recommended ({redundancy})", installed_unit_count(redundancy, n_run),
          "units", f"{redundancy} applied to n", f"n = {n_run}", reference="uptime-tiers")
    r.add("installed_kw", "Installed generator capacity", per_unit * quantity, "kW",
          "Installed = unit kW × quantity", f"{fmt(per_unit)} × {quantity}")
    n_use = usable_units(quantity, redundancy)
    usable = r.add("usable_kw", "Usable capacity (after redundancy)", per_unit * n_use, "kW",
                   f"Usable = unit kW × units available under {redundancy}", f"{fmt(per_unit)} × {n_use}")
    r.add("n_minus_1_kw", "Capacity with one unit out (N−1)", per_unit * max(quantity - 1, 0), "kW",
          "N−1 capacity = unit kW × (quantity − 1)", f"{fmt(per_unit)} × {max(quantity - 1, 0)}")
    if usable > 0:
        r.add("loading_pct", "Generator utilization", load / usable * 100, "%",
              "Utilization = Load kW / Usable kW × 100", f"{fmt(load)} / {fmt(usable)} × 100")
    r.add("reserve_kw", "Reserve capacity", usable - load, "kW", "Reserve = Usable kW − Load kW",
          f"{fmt(usable)} − {fmt(load)}")
    r.add("capacity_ok", "Usable capacity ≥ backed load", usable >= load, "", "Usable kW ≥ Load kW",
          f"{fmt(usable)} ≥ {fmt(load)}")
    r.add("max_step_kw", "Maximum single load step", usable * step_load_pct / 100, "kW",
          "Max step = Usable kW × step-load limit", f"{fmt(usable)} × {fmt(step_load_pct)} / 100",
          assumption="Step-load acceptance from manufacturer data; loads above this need sequencing.",
          reference="manufacturer-data")
    return r
