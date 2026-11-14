"""Site environment checks and user-supplied manufacturer derating.

No manufacturer derating curves are invented. The engine only multiplies rated
capacity by the factors the user enters from manufacturer data, and flags conditions
where derating is likely to be needed.
"""

from __future__ import annotations

from app.calculations import units
from app.calculations.trace import ModuleResult, fmt

# Planning envelopes per equipment class (°C). Verify against the ASHRAE edition in use.
ASHRAE_ENVELOPES_C: dict[str, dict[str, float]] = {
    "A1": {"recommended_min": 18, "recommended_max": 27, "allowable_min": 15, "allowable_max": 32},
    "A2": {"recommended_min": 18, "recommended_max": 27, "allowable_min": 10, "allowable_max": 35},
    "A3": {"recommended_min": 18, "recommended_max": 27, "allowable_min": 5, "allowable_max": 40},
    "A4": {"recommended_min": 18, "recommended_max": 27, "allowable_min": 5, "allowable_max": 45},
}


def derated_capacity(rated: float, temperature_factor: float, altitude_factor: float) -> float:
    return rated * temperature_factor * altitude_factor


def compute_environment(
    *,
    ambient_temp: float,
    temp_unit: str,
    altitude: float,
    altitude_unit: str,
    ashrae_class: str,
    humidity_pct: float | None,
    temperature_factor: float,
    altitude_factor: float,
) -> ModuleResult:
    r = ModuleResult("environment")
    t_c = units.temp_to_c(ambient_temp, temp_unit)
    alt_m = units.length_to_m(altitude, altitude_unit)
    r.add("ambient_c", "Ambient / inlet temperature", t_c, "°C",
          "Input" if temp_unit == "C" else "°C = (°F − 32) × 5/9",
          fmt(ambient_temp) if temp_unit == "C" else f"({fmt(ambient_temp)} − 32) × 5/9")
    r.add("ambient_f", "Ambient / inlet temperature", units.c_to_f(t_c), "°F",
          "Input" if temp_unit == "F" else "°F = °C × 9/5 + 32",
          fmt(ambient_temp) if temp_unit == "F" else f"{fmt(t_c)} × 9/5 + 32")
    r.add("altitude_m", "Site altitude", alt_m, "m", "Input" if altitude_unit == "m" else "m = ft × 0.3048",
          fmt(altitude) if altitude_unit == "m" else f"{fmt(altitude)} × 0.3048")
    r.add("altitude_ft", "Site altitude", units.m_to_ft(alt_m), "ft",
          "Input" if altitude_unit == "ft" else "ft = m / 0.3048",
          fmt(altitude) if altitude_unit == "ft" else f"{fmt(alt_m)} / 0.3048")
    env = ASHRAE_ENVELOPES_C[ashrae_class]
    r.data["ashrae_class"] = ashrae_class
    r.data["envelope_c"] = env
    if humidity_pct is not None:
        r.add("humidity_pct", "Relative humidity", humidity_pct, "%", "Input", fmt(humidity_pct))
    r.add("temperature_factor", "Temperature derate factor", temperature_factor, "×", "Input (manufacturer data)",
          fmt(temperature_factor), reference="manufacturer-data")
    r.add("altitude_factor", "Altitude derate factor", altitude_factor, "×", "Input (manufacturer data)",
          fmt(altitude_factor), reference="manufacturer-data")
    r.add("combined_factor", "Combined derate factor", derated_capacity(1.0, temperature_factor, altitude_factor), "×",
          "Derated capacity = Rated × temperature factor × altitude factor",
          f"1 × {fmt(temperature_factor)} × {fmt(altitude_factor)}",
          assumption="Applied to generator and cooling unit capacity when derating is enabled.")
    return r
