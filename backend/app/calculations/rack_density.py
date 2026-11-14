"""Area density, white space and rack-density classification."""

from __future__ import annotations

from app.calculations import cooling, electrical, units
from app.calculations.trace import ModuleResult, fmt
from app.constants.cooling import THERMAL_TIERS


def area_density_w(it_kw: float, area: float) -> float:
    if area <= 0:
        raise ValueError("area must be greater than zero")
    return it_kw * 1000 / area


def area_per_rack(area: float, rack_count: int) -> float:
    return area / rack_count


def classify_thermal(kw_per_rack: float) -> dict:
    for tier in THERMAL_TIERS:
        upper = tier["max_kw"]
        if upper is None or kw_per_rack <= upper:
            return tier
    return THERMAL_TIERS[-1]


def compute_space(*, it_kw: float, rack_count: int, area_value: float, area_unit: str) -> ModuleResult:
    r = ModuleResult("space")
    ft2 = units.area_to_ft2(area_value, area_unit)
    m2 = units.ft2_to_m2(ft2)
    if area_unit == "ft2":
        r.add("area_ft2", "Room area", ft2, "ft²", "Input", fmt(area_value))
        r.add("area_m2", "Room area", m2, "m²", "m² = ft² × 0.09290304", f"{fmt(ft2)} × 0.09290304",
              reference="physics-conversion")
    else:
        r.add("area_m2", "Room area", m2, "m²", "Input", fmt(area_value))
        r.add("area_ft2", "Room area", ft2, "ft²", "ft² = m² / 0.09290304", f"{fmt(m2)} / 0.09290304",
              reference="physics-conversion")
    r.add("w_per_ft2", "Area density", area_density_w(it_kw, ft2), "W/ft²",
          "W/ft² = IT kW × 1000 / Area ft²", f"{fmt(it_kw)} × 1000 / {fmt(ft2)}",
          assumption="IT load spread over the entered room (white-space) area.")
    r.add("w_per_m2", "Area density", area_density_w(it_kw, m2), "W/m²",
          "W/m² = IT kW × 1000 / Area m²", f"{fmt(it_kw)} × 1000 / {fmt(m2)}")
    r.add("ft2_per_rack", "Area per rack", area_per_rack(ft2, rack_count), "ft²/rack",
          "Area per rack = Area / Racks", f"{fmt(ft2)} / {rack_count}")
    r.add("m2_per_rack", "Area per rack", area_per_rack(m2, rack_count), "m²/rack",
          "Area per rack = Area / Racks", f"{fmt(m2)} / {rack_count}")
    return r


def compute_rack_density(
    *,
    rack_count: int,
    kw_per_rack: float,
    area_value: float | None,
    area_unit: str,
    voltage: float,
    current: float,
    phase: str,
    continuous_factor: float,
    power_factor: float,
) -> dict[str, ModuleResult]:
    """Rack-density tool. Returns the modules it composes (no formulas duplicated)."""
    r = ModuleResult("rack_density")
    it_kw = r.add("it_kw", "Total IT load", rack_count * kw_per_rack, "kW",
                  "IT kW = Racks × kW per rack", f"{rack_count} × {fmt(kw_per_rack)}")
    r.add("kw_per_rack", "Load per rack", kw_per_rack, "kW/rack", "Input", fmt(kw_per_rack))
    cls = cooling.classify_cooling(kw_per_rack)
    tier = classify_thermal(kw_per_rack)
    r.add("cooling_class", "Cooling class", cls["name"], "", "Band lookup on kW/rack", f"{fmt(kw_per_rack)} kW/rack",
          assumption=cls["description"])
    r.add("thermal_class", "Thermal classification", tier["name"], "", "Band lookup on kW/rack",
          f"{fmt(kw_per_rack)} kW/rack")
    r.data["cooling_class"] = cls
    r.data["thermal_class"] = tier
    out = {"rack_density": r}
    out["cooling"] = cooling.compute_cooling(it_kw=it_kw, rack_count=rack_count, kw_per_rack=kw_per_rack)
    out["circuit"] = electrical.compute_circuit(
        voltage=voltage, current=current, phase=phase, continuous_factor=continuous_factor,
        rack_kw=kw_per_rack, power_factor=power_factor,
    )
    if area_value:
        out["space"] = compute_space(it_kw=it_kw, rack_count=rack_count, area_value=area_value, area_unit=area_unit)
    return out
