"""Unit conversions. Every conversion used anywhere in the application lives here."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.calculations import electrical
from app.calculations.trace import ModuleResult, fmt
from app.constants.units import BTU_HR_PER_KW, BTU_HR_PER_TON, KW_PER_MW, M2_PER_FT2, M_PER_FT


def f_to_c(f: float) -> float:
    return (f - 32) * 5 / 9


def c_to_f(c: float) -> float:
    return c * 9 / 5 + 32


def ft2_to_m2(ft2: float) -> float:
    return ft2 * M2_PER_FT2


def m2_to_ft2(m2: float) -> float:
    return m2 / M2_PER_FT2


def ft_to_m(ft: float) -> float:
    return ft * M_PER_FT


def m_to_ft(m: float) -> float:
    return m / M_PER_FT


def kw_to_mw(kw: float) -> float:
    return kw / KW_PER_MW


def mw_to_kw(mw: float) -> float:
    return mw * KW_PER_MW


def kw_to_btu_hr(kw: float) -> float:
    return kw * BTU_HR_PER_KW


def btu_hr_to_kw(btu: float) -> float:
    return btu / BTU_HR_PER_KW


def btu_hr_to_tons(btu: float) -> float:
    return btu / BTU_HR_PER_TON


def tons_to_btu_hr(tons: float) -> float:
    return tons * BTU_HR_PER_TON


def area_to_ft2(value: float, unit: str) -> float:
    return value if unit == "ft2" else m2_to_ft2(value)


def temp_to_c(value: float, unit: str) -> float:
    return value if unit == "C" else f_to_c(value)


def length_to_m(value: float, unit: str) -> float:
    return value if unit == "m" else ft_to_m(value)


@dataclass(frozen=True)
class Conversion:
    id: str
    label: str
    from_unit: str
    to_unit: str
    formula: str
    func: Callable[..., float]
    needs: tuple[str, ...] = ()


def _amps_to_kva(value: float, voltage: float, phase: str) -> float:
    return electrical.circuit_kva(voltage, value, phase)


def _kva_to_amps(value: float, voltage: float, phase: str) -> float:
    return electrical.line_current(value, voltage, phase)


def _kw_to_kva(value: float, power_factor: float) -> float:
    return electrical.kva_from_kw(value, power_factor)


def _kva_to_kw(value: float, power_factor: float) -> float:
    return electrical.kw_from_kva(value, power_factor)


CONVERSIONS: dict[str, Conversion] = {
    c.id: c
    for c in [
        Conversion("f_to_c", "°F → °C", "°F", "°C", "°C = (°F − 32) × 5/9", f_to_c),
        Conversion("c_to_f", "°C → °F", "°C", "°F", "°F = °C × 9/5 + 32", c_to_f),
        Conversion("ft2_to_m2", "ft² → m²", "ft²", "m²", "m² = ft² × 0.09290304", ft2_to_m2),
        Conversion("m2_to_ft2", "m² → ft²", "m²", "ft²", "ft² = m² / 0.09290304", m2_to_ft2),
        Conversion("ft_to_m", "ft → m", "ft", "m", "m = ft × 0.3048", ft_to_m),
        Conversion("m_to_ft", "m → ft", "m", "ft", "ft = m / 0.3048", m_to_ft),
        Conversion("kw_to_mw", "kW → MW", "kW", "MW", "MW = kW / 1000", kw_to_mw),
        Conversion("mw_to_kw", "MW → kW", "MW", "kW", "kW = MW × 1000", mw_to_kw),
        Conversion("kw_to_btu_hr", "kW → BTU/hr", "kW", "BTU/hr", "BTU/hr = kW × 3412.142", kw_to_btu_hr),
        Conversion("btu_hr_to_kw", "BTU/hr → kW", "BTU/hr", "kW", "kW = BTU/hr / 3412.142", btu_hr_to_kw),
        Conversion("btu_hr_to_tons", "BTU/hr → tons", "BTU/hr", "tons", "tons = BTU/hr / 12000", btu_hr_to_tons),
        Conversion("tons_to_btu_hr", "tons → BTU/hr", "tons", "BTU/hr", "BTU/hr = tons × 12000", tons_to_btu_hr),
        Conversion("kw_to_kva", "kW → kVA", "kW", "kVA", "kVA = kW / PF", _kw_to_kva, ("power_factor",)),
        Conversion("kva_to_kw", "kVA → kW", "kVA", "kW", "kW = kVA × PF", _kva_to_kw, ("power_factor",)),
        Conversion("amps_to_kva", "A → kVA", "A", "kVA", "kVA = V × A / 1000  (×√3 for three-phase)",
                   _amps_to_kva, ("voltage", "phase")),
        Conversion("kva_to_amps", "kVA → A", "kVA", "A", "A = kVA × 1000 / V  (/√3 for three-phase)",
                   _kva_to_amps, ("voltage", "phase")),
    ]
}


def convert(conversion_id: str, value: float, **params: float | str) -> ModuleResult:
    conv = CONVERSIONS.get(conversion_id)
    if conv is None:
        raise ValueError(f"unknown conversion '{conversion_id}'")
    kwargs = {}
    for name in conv.needs:
        if params.get(name) is None:
            raise ValueError(f"conversion '{conversion_id}' requires '{name}'")
        kwargs[name] = params[name]
    result = conv.func(value, **kwargs)
    r = ModuleResult("convert")
    extra = ", ".join(f"{k}={fmt(v)}" for k, v in kwargs.items())
    r.add("result", conv.label, result, conv.to_unit, conv.formula,
          f"{fmt(value)} {conv.from_unit}" + (f" ({extra})" if extra else ""),
          reference="physics-conversion")
    return r


def list_conversions() -> list[dict]:
    return [
        {"id": c.id, "label": c.label, "from_unit": c.from_unit, "to_unit": c.to_unit,
         "formula": c.formula, "needs": list(c.needs)}
        for c in CONVERSIONS.values()
    ]
