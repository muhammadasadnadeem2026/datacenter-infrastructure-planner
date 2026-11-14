"""IT load: rack-average and device-list modes."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from app.calculations import electrical
from app.calculations.trace import ModuleResult, fmt


class DeviceLike(Protocol):
    equipment_type: str
    description: str
    quantity: int
    nameplate_w: float
    utilization_pct: float
    rack: str


def rack_average_it_kw(rack_count: int, kw_per_rack: float) -> float:
    return rack_count * kw_per_rack


def device_power_w(quantity: int, nameplate_w: float, utilization_fraction: float) -> float:
    return quantity * nameplate_w * utilization_fraction


def per_rack_kw(it_kw: float, rack_count: int) -> float:
    if rack_count < 1:
        raise ValueError("rack count must be at least 1")
    return it_kw / rack_count


def operating_load_kw(design_kw: float, utilization_fraction: float) -> float:
    return design_kw * utilization_fraction


def device_rows(devices: Sequence[DeviceLike]) -> list[dict[str, Any]]:
    rows = []
    for i, d in enumerate(devices):
        rows.append({
            "index": i,
            "equipment_type": d.equipment_type,
            "description": d.description,
            "quantity": d.quantity,
            "nameplate_w": d.nameplate_w,
            "utilization_pct": d.utilization_pct,
            "rack": d.rack or "Unassigned",
            "calculated_w": device_power_w(d.quantity, d.nameplate_w, d.utilization_pct / 100),
        })
    return rows


def rack_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    racks: dict[str, dict[str, Any]] = {}
    for row in rows:
        entry = racks.setdefault(row["rack"], {"rack": row["rack"], "devices": 0, "watts": 0.0})
        entry["devices"] += row["quantity"]
        entry["watts"] += row["calculated_w"]
    return [{**v, "kw": v["watts"] / 1000} for v in racks.values()]


def compute_it_load(
    *,
    input_mode: str,
    rack_count: int,
    kw_per_rack: float,
    power_factor: float,
    utilization_pct: float = 100.0,
    devices: Sequence[DeviceLike] = (),
) -> ModuleResult:
    r = ModuleResult("it")
    r.data["input_mode"] = input_mode
    if input_mode == "device_list":
        rows = device_rows(devices)
        total_w = sum(row["calculated_w"] for row in rows)
        r.data["devices"] = rows
        r.data["rack_summary"] = rack_summary(rows)
        terms = " + ".join(
            f"{row['quantity']}×{fmt(row['nameplate_w'])}×{fmt(row['utilization_pct'] / 100)}" for row in rows[:6]
        ) + (" + …" if len(rows) > 6 else "")
        r.add("device_total_w", "Total device power", total_w, "W",
              "Σ Device W = Σ (Qty × Nameplate W × Utilization)", terms or "0",
              assumption="Expected utilization is the sustained draw as a share of nameplate.")
        it_kw = r.add("it_kw", "IT load", total_w / 1000, "kW", "IT kW = Σ Device W / 1000",
                      f"{fmt(total_w)} / 1000")
    else:
        it_kw = r.add("it_kw", "IT load", rack_average_it_kw(rack_count, kw_per_rack), "kW",
                      "IT kW = Racks × kW per rack", f"{rack_count} × {fmt(kw_per_rack)}",
                      assumption="Design (peak) IT load used for all infrastructure sizing.")
    r.add("rack_count", "Racks", rack_count, "racks", "Input", str(rack_count))
    per_rack = r.add("kw_per_rack", "Average load per rack", per_rack_kw(it_kw, rack_count), "kW/rack",
                     "kW per rack = IT kW / Racks", f"{fmt(it_kw)} / {rack_count}")
    r.add("power_factor", "Power factor", power_factor, "", "Input", fmt(power_factor))
    r.add("it_kva", "Apparent power", electrical.kva_from_kw(it_kw, power_factor), "kVA",
          "kVA = kW / PF", f"{fmt(it_kw)} / {fmt(power_factor)}")
    r.add("it_mw", "IT load", it_kw / 1000, "MW", "MW = kW / 1000", f"{fmt(it_kw)} / 1000")
    util = utilization_pct / 100
    r.add("operating_it_kw", "Average operating IT load", operating_load_kw(it_kw, util), "kW",
          "Operating kW = IT kW × average utilization", f"{fmt(it_kw)} × {fmt(util)}",
          assumption="Average utilization applies to energy estimates only; sizing uses design load.")
    r.data["per_rack_kw"] = per_rack
    return r
