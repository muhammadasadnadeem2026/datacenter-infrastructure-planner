"""Facility power from PUE and the non-IT overhead split."""

from __future__ import annotations

from app.calculations import electrical
from app.calculations.trace import ModuleResult, fmt


def facility_kw(it_kw: float, pue: float) -> float:
    if pue < 1:
        raise ValueError("PUE must be >= 1")
    return it_kw * pue


def overhead_kw(facility: float, it_kw: float) -> float:
    return facility - it_kw


def share_pct(part: float, whole: float) -> float:
    if whole <= 0:
        raise ValueError("whole must be > 0")
    return part / whole * 100


def compute_facility(
    *,
    it_kw: float,
    pue: float,
    power_factor: float,
    cooling_share_pct: float | None = None,
    electrical_loss_share_pct: float | None = None,
    other_share_pct: float | None = None,
) -> ModuleResult:
    r = ModuleResult("facility")
    r.add("pue", "PUE", pue, "", "Input", fmt(pue), reference="green-grid-pue")
    fac = r.add("facility_kw", "Facility power", facility_kw(it_kw, pue), "kW",
                "Facility kW = IT kW × PUE", f"{fmt(it_kw)} × {fmt(pue)}",
                assumption="PUE applied at design IT load.", reference="green-grid-pue")
    r.add("facility_mw", "Facility power", fac / 1000, "MW", "MW = kW / 1000", f"{fmt(fac)} / 1000")
    r.add("facility_kva", "Facility apparent power", electrical.kva_from_kw(fac, power_factor), "kVA",
          "kVA = Facility kW / PF", f"{fmt(fac)} / {fmt(power_factor)}",
          assumption="Facility-level power factor (defaults to the IT power factor).")
    ovh = r.add("overhead_kw", "Infrastructure overhead", overhead_kw(fac, it_kw), "kW",
                "Overhead = Facility kW − IT kW", f"{fmt(fac)} − {fmt(it_kw)}")
    it_pct = r.add("it_pct", "IT share of facility power", share_pct(it_kw, fac), "%",
                   "IT % = IT kW / Facility kW × 100", f"{fmt(it_kw)} / {fmt(fac)} × 100")
    r.add("overhead_pct", "Infrastructure share", 100 - it_pct, "%", "Overhead % = 100 − IT %",
          f"100 − {fmt(it_pct)}")

    shares = {
        "cooling": cooling_share_pct,
        "electrical_losses": electrical_loss_share_pct,
        "other": other_share_pct,
    }
    labels = {"cooling": "Cooling", "electrical_losses": "Electrical losses", "other": "Other loads"}
    split_given = any(v is not None for v in shares.values())
    r.data["split_given"] = split_given
    breakdown = [{"id": "it", "label": "IT load", "kw": it_kw}]
    if split_given:
        allocated = 0.0
        for key, pct in shares.items():
            pct = pct or 0.0
            kw = r.add(f"{key}_kw", labels[key], ovh * pct / 100, "kW",
                       f"{labels[key]} kW = Overhead × share", f"{fmt(ovh)} × {fmt(pct)} / 100",
                       assumption="User-entered share of facility overhead.")
            allocated += kw
            breakdown.append({"id": key, "label": labels[key], "kw": kw})
        rest = r.add("unallocated_kw", "Unallocated overhead", ovh - allocated, "kW",
                     "Unallocated = Overhead − allocated shares", f"{fmt(ovh)} − {fmt(allocated)}")
        if rest > 1e-9:
            breakdown.append({"id": "unallocated", "label": "Unallocated overhead", "kw": rest})
    else:
        breakdown.append({"id": "overhead", "label": "Facility Overhead", "kw": ovh})
    r.data["breakdown"] = breakdown
    return r
