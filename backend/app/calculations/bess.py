"""Battery energy storage system sizing. AC (PCS) and DC (battery) quantities are kept separate."""

from __future__ import annotations

from app.calculations.trace import ModuleResult, fmt, safe_ceil


def load_energy_mwh(power_mw: float, runtime_hours: float) -> float:
    return power_mw * runtime_hours


def battery_energy_required_mwh(
    load_mwh: float, pcs_efficiency: float, battery_efficiency: float, dod: float, eol_factor: float
) -> float:
    for name, v in (("PCS efficiency", pcs_efficiency), ("battery efficiency", battery_efficiency),
                    ("depth of discharge", dod), ("EOL factor", eol_factor)):
        if not 0 < v <= 1:
            raise ValueError(f"{name} must be in (0, 1]")
    return load_mwh / (pcs_efficiency * battery_efficiency * dod * eol_factor)


def dc_current_a(power_w: float, voltage_dc: float) -> float:
    if voltage_dc <= 0:
        raise ValueError("DC voltage must be > 0")
    return power_w / voltage_dc


def compute_bess(
    *,
    power_mw: float,
    power_basis_note: str,
    duration_min: float,
    dc_bus_voltage: float,
    pcs_efficiency: float,
    battery_efficiency: float,
    depth_of_discharge: float,
    eol_capacity_factor: float,
    redundancy: str,
    container_power_mw: float,
    container_energy_mwh: float,
) -> ModuleResult:
    r = ModuleResult("bess")
    r.data["redundancy"] = redundancy
    hours = duration_min / 60
    p = r.add("required_mw", "Required AC power", power_mw, "MW", "Input / load basis", fmt(power_mw),
              assumption=power_basis_note)
    r.add("duration_h", "Backup duration", hours, "h", "h = min / 60", f"{fmt(duration_min)} / 60")
    e_load = r.add("load_mwh", "Required load energy (AC)", load_energy_mwh(p, hours), "MWh",
                   "E_load = P_MW × runtime h", f"{fmt(p)} × {fmt(hours)}")
    e_batt = r.add(
        "battery_mwh", "Required battery nameplate energy (DC, BOL)",
        battery_energy_required_mwh(
            e_load, pcs_efficiency, battery_efficiency, depth_of_discharge, eol_capacity_factor
        ),
        "MWh", "E_batt = E_load / (η_PCS × η_batt × DoD × EOL)",
        f"{fmt(e_load)} / ({fmt(pcs_efficiency)} × {fmt(battery_efficiency)} × {fmt(depth_of_discharge)} × "
        f"{fmt(eol_capacity_factor)})",
        assumption="Container energy is treated as beginning-of-life nameplate so DoD and EOL are applied once.",
    )
    dc_mw = r.add("dc_power_mw", "Battery DC discharge power", p / pcs_efficiency, "MW",
                  "P_DC = P_AC / η_PCS", f"{fmt(p)} / {fmt(pcs_efficiency)}")
    n_p = r.add("containers_power", "Power-based container count", max(1, safe_ceil(p / container_power_mw)),
                "containers", "ceil(Required MW / Container MW)", f"ceil({fmt(p)} / {fmt(container_power_mw)})")
    n_e = r.add("containers_energy", "Energy-based container count",
                max(1, safe_ceil(e_batt / container_energy_mwh)), "containers",
                "ceil(Required MWh / Container MWh)", f"ceil({fmt(e_batt)} / {fmt(container_energy_mwh)})")
    n_base = r.add("containers_required", "Containers required (N)", max(n_p, n_e), "containers",
                   "max(power-based, energy-based)", f"max({n_p}, {n_e})")
    r.add("sizing_driver", "Sizing driver", "energy" if n_e > n_p else "power" if n_p > n_e else "balanced", "",
          "Larger of the two counts", f"power {n_p} vs energy {n_e}")
    spare = 1 if redundancy == "N+1" else 0
    n = r.add("containers_total", f"Final BESS container count ({redundancy})", n_base + spare, "containers",
              "Total = Required + redundant", f"{n_base} + {spare}", reference="uptime-tiers")
    inst_mw = r.add("installed_mw", "Installed PCS power (AC)", n * container_power_mw, "MW",
                    "Installed MW = containers × container MW", f"{n} × {fmt(container_power_mw)}")
    inst_mwh = r.add("installed_mwh", "Installed battery energy (DC nameplate)", n * container_energy_mwh, "MWh",
                     "Installed MWh = containers × container MWh", f"{n} × {fmt(container_energy_mwh)}")
    r.add("usable_mw", "Usable PCS power (redundant out)", n_base * container_power_mw, "MW",
          "Usable MW = required containers × container MW", f"{n_base} × {fmt(container_power_mw)}")
    r.add("power_margin_pct", "Power spare margin", (inst_mw - p) / p * 100, "%",
          "Margin = (Installed MW − Required MW) / Required MW × 100", f"({fmt(inst_mw)} − {fmt(p)}) / {fmt(p)} × 100")
    r.add("energy_margin_pct", "Energy spare margin", (inst_mwh - e_batt) / e_batt * 100, "%",
          "Margin = (Installed MWh − Required MWh) / Required MWh × 100",
          f"({fmt(inst_mwh)} − {fmt(e_batt)}) / {fmt(e_batt)} × 100")
    i_dc = r.add("dc_current_a", "Total DC current", dc_current_a(dc_mw * 1e6, dc_bus_voltage), "A",
                 "I_DC = P_DC (W) / V_DC", f"{fmt(dc_mw * 1e6)} / {fmt(dc_bus_voltage)}",
                 assumption="At nominal DC bus voltage; all containers in parallel.")
    r.add("dc_current_per_container_a", "DC current per container (N sharing)", i_dc / n_base, "A",
          "I per container = I_DC / required containers", f"{fmt(i_dc)} / {n_base}")
    return r
