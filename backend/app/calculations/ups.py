"""UPS sizing with redundancy, plus an optional battery-energy module.

Runtime is never derived from kVA alone: the battery module requires battery-specific
energy data and still produces only an idealized estimate.
"""

from __future__ import annotations

from app.calculations import electrical
from app.calculations.redundancy import installed_unit_count, redundancy_multiplier, units_needed
from app.calculations.trace import ModuleResult, fmt


def required_ups_kva(load_kva: float, target_fraction: float) -> float:
    if not 0 < target_fraction <= 1:
        raise ValueError("target load fraction must be in (0, 1]")
    return load_kva / target_fraction


def multiplier_formula(redundancy: str) -> str:
    return {"N": "1.0", "N+1": "(n + 1) / n", "2N": "2.0"}[redundancy]


def compute_ups(
    *,
    load_kw: float,
    power_factor: float,
    target_load_pct: float,
    redundancy: str,
    modules_n: int,
    module_kva: float = 0.0,
) -> ModuleResult:
    r = ModuleResult("ups")
    r.data["redundancy"] = redundancy
    r.data["modules_n"] = modules_n
    target = target_load_pct / 100
    load_kva = r.add("load_kva", "UPS load", electrical.kva_from_kw(load_kw, power_factor), "kVA",
                     "Load kVA = IT kW / PF", f"{fmt(load_kw)} / {fmt(power_factor)}")
    base = r.add("required_kva", "Required UPS capacity before redundancy", required_ups_kva(load_kva, target), "kVA",
                 "Required kVA = Load kVA / target load fraction", f"{fmt(load_kva)} / {fmt(target)}",
                 assumption=f"UPS sized so the N capacity runs at {fmt(target_load_pct)} % at design load.")
    mult = r.add("redundancy_multiplier", "Redundancy multiplier", redundancy_multiplier(redundancy, modules_n), "×",
                 f"{redundancy}: {multiplier_formula(redundancy)}",
                 f"n = {modules_n}" if redundancy == "N+1" else redundancy, reference="uptime-tiers")
    count = r.add("module_count", "Installed UPS modules", installed_unit_count(redundancy, modules_n), "modules",
                  f"{redundancy} with n = {modules_n}", f"n = {modules_n}")
    if module_kva > 0:
        r.data["sizing"] = "fixed_module"
        size = r.add("module_kva", "UPS module size", module_kva, "kVA", "Input (selected module rating)",
                     fmt(module_kva))
        installed = r.add("installed_kva", "Installed UPS capacity", size * count, "kVA",
                          "Installed = Module kVA × modules", f"{fmt(size)} × {count}")
        r.add("modules_required_n", "Modules required to carry load (n)", units_needed(base, size), "modules",
              "n required = ceil(Required kVA / Module kVA)", f"ceil({fmt(base)} / {fmt(size)})")
    else:
        r.data["sizing"] = "auto"
        installed = r.add("installed_kva", "Installed UPS capacity", base * mult, "kVA",
                          "Installed = Required kVA × redundancy multiplier", f"{fmt(base)} × {fmt(mult)}")
        size = r.add("module_kva", "UPS module size", installed / count, "kVA",
                     "Module kVA = Installed kVA / installed modules", f"{fmt(installed)} / {count}")
        r.add("modules_required_n", "Modules required to carry load (n)", modules_n, "modules", "Input", str(modules_n))
    usable = r.add("usable_kva", "Usable capacity (redundant modules excluded)", size * modules_n, "kVA",
                   "Usable = Module kVA × n", f"{fmt(size)} × {modules_n}")
    r.add("utilization_installed_pct", "Utilization of installed capacity", load_kva / installed * 100, "%",
          "Utilization = Load kVA / Installed kVA × 100", f"{fmt(load_kva)} / {fmt(installed)} × 100")
    r.add("utilization_usable_pct", "Utilization of usable (N) capacity", load_kva / usable * 100, "%",
          "Utilization = Load kVA / Usable kVA × 100", f"{fmt(load_kva)} / {fmt(usable)} × 100")
    r.add("target_load_pct", "Target UPS loading", target_load_pct, "%", "Input", fmt(target_load_pct))
    return r


def compute_battery(
    *,
    load_kw: float,
    chemistry: str,
    nominal_voltage: float,
    capacity_kwh: float,
    capacity_ah: float,
    discharge_efficiency: float,
    degradation_pct: float,
    runtime_target_min: float,
) -> ModuleResult:
    r = ModuleResult("battery")
    r.data["chemistry"] = chemistry
    if capacity_kwh > 0:
        nameplate = r.add("nameplate_kwh", "Battery nameplate energy", capacity_kwh, "kWh", "Input", fmt(capacity_kwh))
    elif capacity_ah > 0:
        nameplate = r.add("nameplate_kwh", "Battery nameplate energy", nominal_voltage * capacity_ah / 1000, "kWh",
                          "kWh = V × Ah / 1000", f"{fmt(nominal_voltage)} × {fmt(capacity_ah)} / 1000")
    else:
        raise ValueError("battery capacity (kWh or Ah) is required")
    health = 1 - degradation_pct / 100
    available = r.add("available_kwh", "Deliverable energy", nameplate * health * discharge_efficiency, "kWh",
                      "Deliverable = Nameplate × (1 − degradation) × discharge efficiency",
                      f"{fmt(nameplate)} × {fmt(health)} × {fmt(discharge_efficiency)}")
    r.add("runtime_min", "Idealized runtime at design load", available / load_kw * 60, "min",
          "Runtime = Deliverable kWh / Load kW × 60", f"{fmt(available)} / {fmt(load_kw)} × 60",
          assumption=("Idealized constant-power estimate. Actual runtime depends on the manufacturer's discharge "
                      "curve (discharge rate, temperature, end-of-discharge voltage, aging). Use manufacturer data."),
          reference="ieee-485-battery")
    r.add("required_kwh", "Nameplate energy needed for target runtime",
          load_kw * runtime_target_min / 60 / (health * discharge_efficiency), "kWh",
          "Required = Load kW × target min / 60 / ((1 − degradation) × efficiency)",
          f"{fmt(load_kw)} × {fmt(runtime_target_min)} / 60 / ({fmt(health)} × {fmt(discharge_efficiency)})")
    r.add("runtime_target_min", "Runtime target", runtime_target_min, "min", "Input", fmt(runtime_target_min))
    r.add("dc_current_a", "Battery discharge current", load_kw / discharge_efficiency * 1000 / nominal_voltage, "A",
          "I_DC = (Load kW / efficiency) × 1000 / V_nominal",
          f"({fmt(load_kw)} / {fmt(discharge_efficiency)}) × 1000 / {fmt(nominal_voltage)}",
          assumption="At nominal voltage; current rises as voltage falls during discharge.")
    return r
