"""Transformer loading, full-load current and approximate terminal fault current."""

from __future__ import annotations

from app.calculations import electrical
from app.calculations.redundancy import installed_unit_count, units_needed, usable_units
from app.calculations.trace import ModuleResult, fmt

FAULT_CURRENT_NOTE = (
    "Approximate transformer-terminal symmetrical fault current assuming an infinite (zero-impedance) source. "
    "Does not replace a proper short-circuit / coordination study."
)


def full_load_current(kva: float, voltage_ll: float) -> float:
    return electrical.line_current(kva, voltage_ll, "three")


def terminal_fault_current(fla: float, impedance_pct: float) -> float:
    if impedance_pct <= 0:
        raise ValueError("impedance must be > 0")
    return fla / (impedance_pct / 100)


def input_kva(output_kva: float, efficiency: float) -> float:
    if not 0 < efficiency <= 1:
        raise ValueError("efficiency must be in (0, 1]")
    return output_kva / efficiency


def compute_transformer(
    *,
    required_kva: float,
    primary_voltage: float,
    secondary_voltage: float,
    kva_rating: float,
    efficiency: float,
    impedance_pct: float,
    quantity: int,
    redundancy: str,
    target_utilization_pct: float,
) -> ModuleResult:
    r = ModuleResult("transformer")
    r.data["redundancy"] = redundancy
    r.data["primary_voltage"] = primary_voltage
    r.data["secondary_voltage"] = secondary_voltage
    r.add("required_kva", "Required transformer capacity (load)", required_kva, "kVA",
          "Facility kVA", fmt(required_kva), assumption="Transformers serve the full facility load.")
    installed = r.add("installed_kva", "Installed transformer capacity", kva_rating * quantity, "kVA",
                      "Installed = Rating × quantity", f"{fmt(kva_rating)} × {quantity}")
    n_use = usable_units(quantity, redundancy)
    usable = r.add("usable_kva", "Usable capacity (after redundancy)", kva_rating * n_use, "kVA",
                   f"Usable = Rating × units available under {redundancy}", f"{fmt(kva_rating)} × {n_use}",
                   reference="uptime-tiers")
    r.add("loading_installed_pct", "Loading of installed capacity", required_kva / installed * 100, "%",
          "Loading = Required kVA / Installed kVA × 100", f"{fmt(required_kva)} / {fmt(installed)} × 100")
    if usable > 0:
        r.add("loading_pct", "Transformer loading (redundant units out)", required_kva / usable * 100, "%",
              "Loading = Required kVA / Usable kVA × 100", f"{fmt(required_kva)} / {fmt(usable)} × 100",
              reference="ieee-c57-transformers")
    r.add("load_per_unit_kva", "Load per transformer (normal sharing)", required_kva / quantity, "kVA",
          "Load per unit = Required kVA / quantity", f"{fmt(required_kva)} / {quantity}")
    target = target_utilization_pct / 100
    n_req = units_needed(required_kva, kva_rating * target)
    r.add("units_required_n", "Transformers needed to carry load at target (n)", n_req, "units",
          "n = ceil(Required kVA / (Rating × target))",
          f"ceil({fmt(required_kva)} / ({fmt(kva_rating)} × {fmt(target)}))")
    r.add("units_recommended", f"Transformers recommended ({redundancy})", installed_unit_count(redundancy, n_req),
          "units", f"{redundancy} applied to n", f"n = {n_req}")
    losses = r.add("losses_kva_approx", "Approximate transformer losses", required_kva * (1 / efficiency - 1), "kVA",
                   "Losses ≈ Required kVA × (1/η − 1)", f"{fmt(required_kva)} × (1/{fmt(efficiency)} − 1)",
                   assumption="Single efficiency value at design load; real losses vary with loading.")
    r.add("input_kva", "Upstream (utility-side) kVA", input_kva(required_kva, efficiency), "kVA",
          "Input kVA = Output kVA / η", f"{fmt(required_kva)} / {fmt(efficiency)}")
    fla_s = r.add("secondary_fla_a", "Secondary full-load current (per unit)",
                  full_load_current(kva_rating, secondary_voltage), "A", "I = kVA × 1000 / (√3 × V_LL)",
                  f"{fmt(kva_rating)} × 1000 / (√3 × {fmt(secondary_voltage)})")
    r.add("primary_fla_a", "Primary full-load current (per unit)", full_load_current(kva_rating, primary_voltage),
          "A", "I = kVA × 1000 / (√3 × V_LL)", f"{fmt(kva_rating)} × 1000 / (√3 × {fmt(primary_voltage)})")
    isc = r.add("fault_current_a", "Approx. terminal fault current (per unit)",
                terminal_fault_current(fla_s, impedance_pct), "A", "I_SC = FLA / (Z% / 100)",
                f"{fmt(fla_s)} / ({fmt(impedance_pct)} / 100)", assumption=FAULT_CURRENT_NOTE,
                reference="ieee-551-short-circuit")
    r.add("fault_current_ka", "Approx. terminal fault current (per unit)", isc / 1000, "kA", "kA = A / 1000",
          f"{fmt(isc)} / 1000", assumption=FAULT_CURRENT_NOTE)
    r.data["losses_kva"] = losses
    return r
