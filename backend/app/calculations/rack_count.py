"""Inverse problem: how many racks of a given rating serve a target IT load."""

from __future__ import annotations

from app.calculations.trace import ModuleResult, fmt, safe_ceil


def racks_required(it_kw: float, rack_power_kw: float) -> int:
    if rack_power_kw <= 0:
        raise ValueError("rack power must be > 0")
    return max(1, safe_ceil(it_kw / rack_power_kw))


def compute_rack_count(*, it_kw: float, rack_power_kw: float, racks_planned: int | None = None) -> ModuleResult:
    r = ModuleResult("rack_count")
    r.add("target_it_kw", "Target IT load", it_kw, "kW", "Input", fmt(it_kw))
    r.add("rack_rating_kw", "Rack power rating", rack_power_kw, "kW/rack", "Input", fmt(rack_power_kw))
    n = r.add("racks_required", "Racks required", racks_required(it_kw, rack_power_kw), "racks",
              "Racks = ceil(IT kW / Rack kW)", f"ceil({fmt(it_kw)} / {fmt(rack_power_kw)})")
    installed = r.add("installed_rack_kw", "Installed rack power", n * rack_power_kw, "kW",
                      "Installed = Racks × Rack kW", f"{n} × {fmt(rack_power_kw)}")
    r.add("unused_kw", "Unused rack capacity", installed - it_kw, "kW", "Unused = Installed − IT kW",
          f"{fmt(installed)} − {fmt(it_kw)}")
    if racks_planned is not None:
        planned = r.add("racks_planned", "Racks planned", racks_planned, "racks", "Input", str(racks_planned))
        cap = r.add("planned_rack_kw", "Planned rack power capacity", planned * rack_power_kw, "kW",
                    "Capacity = Racks planned × Rack kW", f"{planned} × {fmt(rack_power_kw)}")
        r.add("rack_power_loading_pct", "Rack power utilization", it_kw / cap * 100, "%",
              "Utilization = IT kW / Rack capacity × 100", f"{fmt(it_kw)} / {fmt(cap)} × 100")
    return r
