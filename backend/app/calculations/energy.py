"""Annual energy and electricity cost estimate."""

from __future__ import annotations

from app.calculations.it_load import operating_load_kw
from app.calculations.trace import ModuleResult, fmt
from app.constants.units import MONTHS_PER_YEAR


def annual_energy_kwh(kw: float, hours: float) -> float:
    return kw * hours


def energy_cost(kwh: float, rate: float) -> float:
    return kwh * rate


def annual_demand_cost(peak_kw: float, demand_charge_per_kw_month: float) -> float:
    return peak_kw * demand_charge_per_kw_month * MONTHS_PER_YEAR


def compute_energy(
    *,
    it_kw: float,
    facility_kw: float,
    electricity_rate: float,
    demand_charge: float = 0.0,
    hours_per_year: float = 8760,
    utilization_pct: float = 100.0,
    currency: str = "USD",
) -> ModuleResult:
    r = ModuleResult("energy")
    r.data["currency"] = currency
    util = utilization_pct / 100
    util_note = "Design load operating continuously." if util == 1 else f"Average utilization {fmt(utilization_pct)} %."
    avg_it = operating_load_kw(it_kw, util)
    avg_fac = operating_load_kw(facility_kw, util)
    sub_it = (f"{fmt(it_kw)} × {fmt(hours_per_year)}" if util == 1
              else f"{fmt(it_kw)} × {fmt(util)} × {fmt(hours_per_year)}")
    sub_fac = (f"{fmt(facility_kw)} × {fmt(hours_per_year)}" if util == 1
               else f"{fmt(facility_kw)} × {fmt(util)} × {fmt(hours_per_year)}")
    r.add("hours_per_year", "Hours per year", hours_per_year, "h", "Input", fmt(hours_per_year))
    r.add("annual_it_kwh", "Annual IT energy", annual_energy_kwh(avg_it, hours_per_year), "kWh",
          "Annual IT kWh = IT kW × utilization × hours", sub_it, assumption=util_note)
    fac_kwh = r.add("annual_facility_kwh", "Annual facility energy", annual_energy_kwh(avg_fac, hours_per_year),
                    "kWh", "Annual facility kWh = Facility kW × utilization × hours", sub_fac, assumption=util_note)
    r.add("annual_facility_mwh", "Annual facility energy", fac_kwh / 1000, "MWh", "MWh = kWh / 1000",
          f"{fmt(fac_kwh)} / 1000")
    e_cost = r.add("annual_energy_cost", "Annual energy charge", energy_cost(fac_kwh, electricity_rate), currency,
                   "Energy charge = Annual facility kWh × rate", f"{fmt(fac_kwh)} × {fmt(electricity_rate)}",
                   assumption="Flat energy rate. Real tariffs (TOU, tiers, taxes, riders) vary — this is an estimate.")
    d_cost = r.add("annual_demand_cost", "Annual demand charge", annual_demand_cost(facility_kw, demand_charge),
                   currency, "Demand charge = Peak facility kW × $/kW-month × 12",
                   f"{fmt(facility_kw)} × {fmt(demand_charge)} × 12",
                   assumption="Peak demand taken as design facility load every month.")
    total = r.add("annual_cost", "Estimated annual electricity bill", e_cost + d_cost, currency,
                  "Total = Energy charge + Demand charge", f"{fmt(e_cost)} + {fmt(d_cost)}",
                  assumption="Estimate only; utility tariff structures vary.")
    r.add("monthly_cost", "Average monthly bill", total / MONTHS_PER_YEAR, currency, "Monthly = Annual / 12",
          f"{fmt(total)} / 12")
    return r
