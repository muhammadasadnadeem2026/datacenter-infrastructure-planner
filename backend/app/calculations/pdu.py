"""Rack PDU sizing with growth margin and A/B feeds."""

from __future__ import annotations

from app.calculations import electrical
from app.calculations.trace import ModuleResult, fmt


def design_load_kw(rack_kw: float, growth_margin_pct: float) -> float:
    return rack_kw * (1 + growth_margin_pct / 100)


def compute_pdu(
    *,
    rack_kw: float,
    power_factor: float,
    growth_margin_pct: float,
    voltage: float,
    amperage: float,
    phase: str,
    continuous_factor: float,
    feed: str,
) -> ModuleResult:
    r = ModuleResult("pdu")
    r.data["feed"] = feed
    r.data["phase"] = phase
    g = growth_margin_pct / 100
    design = r.add("design_kw", "Design rack load", design_load_kw(rack_kw, growth_margin_pct), "kW",
                   "Design kW = Rack kW × (1 + growth margin)", f"{fmt(rack_kw)} × (1 + {fmt(g)})")
    rack_kva = r.add("rack_kva", "Design rack apparent power", electrical.kva_from_kw(design, power_factor), "kVA",
                     "Rack kVA = Design kW / PF", f"{fmt(design)} / {fmt(power_factor)}")
    rated = r.add("pdu_kva", "PDU rated capacity", electrical.circuit_kva(voltage, amperage, phase), "kVA",
                  electrical.kva_formula(phase), electrical.kva_substitution(voltage, amperage, phase))
    usable = r.add("pdu_usable_kva", "PDU usable capacity", electrical.usable_kva(rated, continuous_factor), "kVA",
                   "Usable = Rated kVA × continuous factor", f"{fmt(rated)} × {fmt(continuous_factor)}",
                   reference="nec-continuous-load")
    per_feed = r.add("pdus_per_feed", "PDUs per feed", electrical.min_circuits(rack_kva, usable), "PDUs",
                     "PDUs per feed = ceil(Rack kVA / Usable PDU kVA)", f"ceil({fmt(rack_kva)} / {fmt(usable)})",
                     assumption=("Each feed carries the full design load on its own (A/B philosophy)."
                                 if feed == "ab" else "Single feed, no distribution redundancy."))
    feeds = 2 if feed == "ab" else 1
    total = r.add("pdus_total", "PDUs per rack", per_feed * feeds, "PDUs",
                  "Total = PDUs per feed × feeds", f"{per_feed} × {feeds}")
    if feed == "ab":
        normal_load = r.add("load_per_pdu_kva", "Load per PDU (normal, shared A/B)", rack_kva / total, "kVA",
                            "Normal load = Rack kVA / total PDUs", f"{fmt(rack_kva)} / {total}")
        r.add("loading_normal_pct", "PDU loading (normal)", normal_load / rated * 100, "%",
              "Loading = Load per PDU / Rated kVA × 100", f"{fmt(normal_load)} / {fmt(rated)} × 100")
    failover = r.add("load_per_pdu_failover_kva", "Load per PDU (one feed lost)" if feed == "ab" else "Load per PDU",
                     rack_kva / per_feed, "kVA", "Load = Rack kVA / PDUs per feed", f"{fmt(rack_kva)} / {per_feed}")
    loading = r.add("loading_pct", "PDU loading (design case)", failover / rated * 100, "%",
                    "Loading = Load per PDU / Rated kVA × 100", f"{fmt(failover)} / {fmt(rated)} × 100",
                    assumption="Design case = one feed carrying the full load." if feed == "ab" else "")
    r.add("loading_of_usable_pct", "PDU loading of usable capacity", failover / usable * 100, "%",
          "Loading = Load per PDU / Usable kVA × 100", f"{fmt(failover)} / {fmt(usable)} × 100")
    caution, critical = electrical.circuit_limits(continuous_factor)
    r.add("status", "PDU loading status", electrical.circuit_status(loading, continuous_factor), "",
          f"≤{fmt(caution)} % normal; ≤{fmt(critical)} % caution; >{fmt(critical)} % fails continuous-load check",
          f"{fmt(loading)} %")
    r.data["limits_pct"] = {"caution": caution, "critical": critical}
    r.add("line_current_a", "Line current per PDU", electrical.line_current(failover, voltage, phase), "A",
          electrical.current_formula(phase), electrical.current_substitution(failover, voltage, phase))
    if phase == "three":
        r.add("kva_per_phase", "Balanced load per phase", failover / 3, "kVA", "kVA per phase = PDU load / 3",
              f"{fmt(failover)} / 3", assumption="Perfectly balanced phases; real racks are rarely balanced.")
    return r
