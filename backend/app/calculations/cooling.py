"""Cooling load: heat rejection, refrigeration tons and density classification."""

from __future__ import annotations

from app.calculations import units
from app.calculations.redundancy import usable_units
from app.calculations.trace import ModuleResult, fmt
from app.constants.cooling import COOLING_CLASSES
from app.constants.units import LPM_PER_GPM


def classify_cooling(kw_per_rack: float) -> dict:
    """Bands are (min, max]; the last band is unbounded."""
    for band in COOLING_CLASSES:
        upper = band["max_kw"]
        if upper is None or kw_per_rack <= upper:
            return band
    return COOLING_CLASSES[-1]


def liquid_heat_kw(total_heat_kw: float, capture_fraction: float) -> float:
    if not 0 <= capture_fraction <= 1:
        raise ValueError("liquid capture must be between 0 and 100 %")
    return total_heat_kw * capture_fraction


def coolant_flow_lpm(it_kw: float, lpm_per_kw: float) -> float:
    return it_kw * lpm_per_kw


def compute_cooling(
    *,
    it_kw: float,
    rack_count: int,
    kw_per_rack: float | None = None,
    additional_heat_kw: float = 0.0,
    additional_heat_note: str = "",
    unit_capacity_kw: float = 0.0,
    unit_count: int = 0,
    redundancy: str = "N",
    capacity_factor: float = 1.0,
    liquid_capture_pct: float = 0.0,
    coolant_flow_lpm_per_kw: float = 0.0,
) -> ModuleResult:
    r = ModuleResult("cooling")
    thermal = r.add("thermal_kw", "IT heat load", it_kw, "kW thermal", "Thermal kW = IT kW",
                    fmt(it_kw), assumption="Essentially all IT electrical power is converted to heat.")
    btu = r.add("btu_hr", "IT heat load", units.kw_to_btu_hr(thermal), "BTU/hr",
                "BTU/hr = kW × 3412.142", f"{fmt(thermal)} × 3412.142", reference="physics-conversion")
    r.add("tons", "Cooling capacity required", units.btu_hr_to_tons(btu), "tons",
          "Tons = BTU/hr / 12000", f"{fmt(btu)} / 12000", reference="physics-conversion")
    r.add("btu_hr_per_rack", "Heat load per rack", btu / rack_count, "BTU/hr/rack",
          "BTU/hr per rack = BTU/hr / Racks", f"{fmt(btu)} / {rack_count}")
    r.add("tons_per_rack", "Cooling per rack", units.btu_hr_to_tons(btu / rack_count), "tons/rack",
          "Tons per rack = (BTU/hr / Racks) / 12000", f"{fmt(btu / rack_count)} / 12000")
    total = r.add("total_heat_kw", "Total room heat load", thermal + additional_heat_kw, "kW thermal",
                  "Total heat = IT heat + additional in-room heat", f"{fmt(thermal)} + {fmt(additional_heat_kw)}",
                  assumption=additional_heat_note or "No additional in-room heat sources entered.")
    total_btu = r.add("total_btu_hr", "Total room heat load", units.kw_to_btu_hr(total), "BTU/hr",
                      "BTU/hr = kW × 3412.142", f"{fmt(total)} × 3412.142")
    r.add("total_tons", "Total cooling required", units.btu_hr_to_tons(total_btu), "tons",
          "Tons = BTU/hr / 12000", f"{fmt(total_btu)} / 12000")
    if liquid_capture_pct > 0:
        capture = liquid_capture_pct / 100
        liquid = r.add("liquid_heat_kw", "Heat to liquid (TCS / CDU)", liquid_heat_kw(total, capture), "kW thermal",
                       "Liquid heat = Total heat × liquid capture ratio", f"{fmt(total)} × {fmt(capture)}",
                       assumption="Liquid:air heat-capture ratio from the rack / equipment vendor.",
                       reference="manufacturer-data")
        air = r.add("air_heat_kw", "Residual heat to room air", total - liquid, "kW thermal",
                    "Air heat = Total heat − Liquid heat", f"{fmt(total)} − {fmt(liquid)}")
        r.add("air_tons", "Room air cooling required", units.btu_hr_to_tons(units.kw_to_btu_hr(air)), "tons",
              "Tons = kW × 3412.142 / 12000", f"{fmt(air)} × 3412.142 / 12000")
        if coolant_flow_lpm_per_kw > 0:
            flow = r.add("coolant_flow_lpm", "Coolant flow (technology cooling system)",
                         coolant_flow_lpm(it_kw, coolant_flow_lpm_per_kw), "L/min",
                         "Flow = IT kW × specific flow (L/min per kW)",
                         f"{fmt(it_kw)} × {fmt(coolant_flow_lpm_per_kw)}",
                         assumption="Specific flow per kW of rack power from the equipment vendor.",
                         reference="manufacturer-data")
            r.add("coolant_flow_gpm", "Coolant flow", flow / LPM_PER_GPM, "US gpm", "gpm = L/min / 3.785411784",
                  f"{fmt(flow)} / 3.785411784", reference="physics-conversion")
            r.add("coolant_flow_lpm_per_rack", "Coolant flow per rack", flow / rack_count, "L/min/rack",
                  "Flow per rack = Flow / Racks", f"{fmt(flow)} / {rack_count}")
    r.data["liquid_capture_pct"] = liquid_capture_pct
    density = kw_per_rack if kw_per_rack is not None else it_kw / rack_count
    cls = classify_cooling(density)
    r.add("classification", "Cooling classification", cls["name"], "", "Band lookup on kW/rack",
          f"{fmt(density)} kW/rack", assumption=cls["description"])
    r.data["classification"] = cls
    if unit_capacity_kw > 0 and unit_count > 0:
        unit_eff = r.add("unit_capacity_kw", "Cooling unit capacity (derated)", unit_capacity_kw * capacity_factor,
                         "kW thermal", "Unit capacity × environmental factor",
                         f"{fmt(unit_capacity_kw)} × {fmt(capacity_factor)}",
                         assumption="Manufacturer capacity at site conditions; factor from Environment module.",
                         reference="manufacturer-data")
        r.add("installed_kw", "Installed cooling capacity", unit_eff * unit_count, "kW thermal",
              "Installed = Unit capacity × Units", f"{fmt(unit_eff)} × {unit_count}")
        n_usable = usable_units(unit_count, redundancy)
        usable = r.add("usable_kw", "Usable cooling capacity (after redundancy)", unit_eff * n_usable,
                       "kW thermal", f"Usable = Unit capacity × units available under {redundancy}",
                       f"{fmt(unit_eff)} × {n_usable}", reference="uptime-tiers")
        r.add("usable_tons", "Usable cooling capacity", units.btu_hr_to_tons(units.kw_to_btu_hr(usable)), "tons",
              "Tons = kW × 3412.142 / 12000", f"{fmt(usable)} × 3412.142 / 12000")
        r.data["redundancy"] = redundancy
    return r
