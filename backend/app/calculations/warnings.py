"""Centralized engineering warning engine.

All warning logic lives here. UI components only render the list returned by the API.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.calculations.trace import ModuleResult, cmp_round
from app.constants import thresholds as T


@dataclass(frozen=True)
class EngineeringWarning:
    severity: str  # info | caution | critical
    code: str
    title: str
    message: str
    affected_system: str
    reference: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


W = EngineeringWarning


def _pct(x: float) -> str:
    return f"{x:.1f} %"


def circuit_warnings(c: ModuleResult) -> list[W]:
    out: list[W] = []
    load = c.v("loading_pct")
    status = c.v("status")
    lim = c.data["limits_pct"]
    existing = c.data.get("evaluated_on") == "existing"
    subject = "Existing rack circuits" if existing else "Rack circuits (at minimum count)"
    if status == "critical":
        out.append(W("critical", "CIRCUIT_OVERLOAD", "Circuit continuous-load check failed",
                     f"{subject} are loaded to {_pct(load)} of rating, above the {lim['critical']:g} % continuous-load "
                     f"limit. At least {c.v('min_circuits')} circuits per rack are required.",
                     "circuit", "nec-continuous-load"))
    elif status == "caution":
        out.append(W("caution", "CIRCUIT_HEADROOM", "Limited circuit headroom",
                     f"{subject} are loaded to {_pct(load)} of rating (caution band "
                     f"{lim['caution']:g}–{lim['critical']:g} %).", "circuit", "nec-continuous-load"))
    return out


def pdu_warnings(p: ModuleResult) -> list[W]:
    out: list[W] = []
    load = p.v("loading_pct")
    status = p.v("status")
    case = "with one feed lost" if p.data.get("feed") == "ab" else "at design load"
    if status == "critical":
        out.append(W("critical", "PDU_OVERLOAD", "PDU loading exceeds continuous limit",
                     f"Each PDU carries {_pct(load)} of its rating {case}.", "pdu", "nec-continuous-load"))
    elif status == "caution":
        out.append(W("caution", "PDU_HEADROOM", "Limited PDU headroom",
                     f"Each PDU carries {_pct(load)} of its rating {case}.", "pdu"))
    if p.data.get("feed") == "none":
        out.append(W("info", "PDU_SINGLE_FEED", "Single rack feed",
                     "Racks have no A/B distribution redundancy; a single PDU or feed failure drops the rack.", "pdu"))
    return out


def ups_warnings(u: ModuleResult) -> list[W]:
    out: list[W] = []
    util = u.v("utilization_usable_pct")
    target = u.v("target_load_pct")
    if cmp_round(util) > 100:
        out.append(W("critical", "UPS_OVERLOAD", "UPS capacity insufficient",
                     f"UPS load is {_pct(util)} of usable (N) capacity. Add modules or increase module size.",
                     "ups", "uptime-tiers"))
    elif cmp_round(util) > cmp_round(target):
        out.append(W("caution", "UPS_ABOVE_TARGET", "UPS above target loading",
                     f"UPS usable capacity is loaded to {_pct(util)}, above the {target:g} % target.", "ups"))
    if u.data.get("sizing") == "fixed_module" and u.v("modules_required_n") > u.data["modules_n"]:
        out.append(W("critical", "UPS_MODULES_SHORT", "Too few UPS modules",
                     f"{u.v('modules_required_n')} modules of {u.v('module_kva'):,.0f} kVA are needed to carry the "
                     f"load at the target loading; n = {u.data['modules_n']} is configured.", "ups"))
    if u.data.get("redundancy") == "N":
        out.append(W("caution", "UPS_NO_REDUNDANCY", "No UPS redundancy",
                     "UPS is configured N: a single module failure or maintenance event may interrupt service.",
                     "ups", "uptime-tiers"))
    return out


def battery_warnings(b: ModuleResult) -> list[W]:
    out = [W("info", "BATTERY_RUNTIME_ESTIMATE", "Battery runtime is an idealized estimate",
             "Runtime requires battery-specific manufacturer discharge data; the value shown assumes constant "
             "power and ignores rate, temperature and end-voltage effects.", "battery", "ieee-485-battery")]
    if cmp_round(b.v("runtime_min")) < cmp_round(b.v("runtime_target_min")):
        out.append(W("critical", "BATTERY_RUNTIME_SHORT", "Battery runtime below target",
                     f"Estimated runtime {b.v('runtime_min'):.1f} min is below the {b.v('runtime_target_min'):g} min "
                     f"target; about {b.v('required_kwh'):,.0f} kWh nameplate is needed.", "battery"))
    return out


def transformer_warnings(t: ModuleResult, target_pct: float) -> list[W]:
    out: list[W] = []
    load = t.get("loading_pct")
    if load is None:
        return out
    if cmp_round(load) > 100:
        out.append(W("critical", "TRANSFORMER_OVERLOAD", "Transformer capacity exceeded",
                     f"Required load is {_pct(load)} of usable transformer capacity with redundant units "
                     "out of service.",
                     "transformer", "ieee-c57-transformers"))
    elif cmp_round(load) > cmp_round(target_pct):
        out.append(W("caution", "TRANSFORMER_ABOVE_TARGET", "Transformer above target utilization",
                     f"Transformer loading {_pct(load)} exceeds the {target_pct:g} % target.", "transformer"))
    if t.data.get("redundancy") == "N":
        out.append(W("caution", "TRANSFORMER_NO_REDUNDANCY", "No transformer redundancy",
                     "Transformers are configured N: loss of one unit reduces capacity below design load.",
                     "transformer", "uptime-tiers"))
    out.append(W("info", "FAULT_CURRENT_APPROX", "Fault current is approximate",
                 "The transformer-terminal fault current assumes an infinite source and does not replace a "
                 "short-circuit study.", "transformer", "ieee-551-short-circuit"))
    return out


def generator_warnings(g: ModuleResult, target_pct: float) -> list[W]:
    out: list[W] = []
    if not g.v("capacity_ok"):
        out.append(W("critical", "GENERATOR_INSUFFICIENT", "Generator capacity insufficient",
                     f"Usable generator capacity {g.v('usable_kw'):,.0f} kW is below the backed load "
                     f"{g.v('critical_load_kw'):,.0f} kW. About {g.v('units_recommended')} units are recommended.",
                     "generator", "manufacturer-data"))
    else:
        load = g.get("loading_pct")
        if load is not None and cmp_round(load) > cmp_round(target_pct):
            out.append(W("caution", "GENERATOR_ABOVE_TARGET", "Generator above target loading",
                         f"Generators are loaded to {_pct(load)}, above the {target_pct:g} % target.", "generator"))
    if g.v("critical_load_kw") > g.v("max_step_kw"):
        out.append(W("info", "GENERATOR_STEP_LOAD", "Load sequencing required",
                     f"Backed load exceeds the single-step limit ({g.v('max_step_kw'):,.0f} kW); transfer loads in "
                     "stages per manufacturer step-load data.", "generator", "manufacturer-data"))
    if g.data.get("redundancy") == "N":
        out.append(W("caution", "GENERATOR_NO_REDUNDANCY", "No generator redundancy",
                     "Generators are configured N: a single unit failure may interrupt backed loads.",
                     "generator", "uptime-tiers"))
    return out


def bess_warnings(b: ModuleResult) -> list[W]:
    out: list[W] = []
    if b.v("dc_current_a") > T.BESS_DC_CURRENT_HIGH_A:
        out.append(W("caution", "BESS_DC_CURRENT_HIGH", "Very high DC current",
                     f"Total DC current is {b.v('dc_current_a'):,.0f} A. Review DC architecture: parallel strings, "
                     "higher DC bus voltage or distributed PCS.", "bess"))
    return out


def cooling_warnings(c: ModuleResult) -> list[W]:
    out: list[W] = []
    cls = c.data["classification"]
    if cls["id"] == "liquid":
        out.append(W("caution", "LIQUID_COOLING_REQUIRED", "Liquid cooling evaluation required",
                     f"Rack density exceeds {T.LIQUID_COOLING_KW_PER_RACK:g} kW/rack. {cls['description']}", "cooling"))
    elif cls["id"] == "hybrid":
        out.append(W("caution", "HIGH_RACK_DENSITY", "High rack density", cls["description"], "cooling"))
    if cls["id"] == "liquid" and not c.data.get("liquid_capture_pct"):
        out.append(W("info", "LIQUID_SPLIT_MISSING", "Liquid / air heat split not entered",
                     "Enter the vendor liquid heat-capture ratio to size the liquid loop and the residual room "
                     "air cooling separately.", "cooling", "manufacturer-data"))
    return out


def density_warnings(space: ModuleResult) -> list[W]:
    if space.v("w_per_ft2") > T.HIGH_AREA_DENSITY_W_PER_FT2:
        return [W("caution", "HIGH_AREA_DENSITY", "High area power density",
                  f"Area density is {space.v('w_per_ft2'):,.0f} W/ft² ({space.v('w_per_m2'):,.0f} W/m²). Review room "
                  "distribution, airflow and floor / rack layout.", "space")]
    return []


def it_warnings(it: ModuleResult) -> list[W]:
    pf = it.v("power_factor")
    if pf < T.PF_REVIEW_BELOW:
        return [W("caution", "LOW_POWER_FACTOR", "Low power factor",
                  f"Power factor {pf:g} is below {T.PF_REVIEW_BELOW:g}. Review equipment characteristics; modern IT "
                  "power supplies are typically higher.", "it")]
    return []


def facility_warnings(f: ModuleResult) -> list[W]:
    pue = f.v("pue")
    if pue < T.PUE_REALISTIC_MIN:
        return [W("caution", "PUE_UNREALISTIC", "PUE below realistic range",
                  f"PUE {pue:g} is below {T.PUE_REALISTIC_MIN:g}. Verify the assumption.",
                  "facility", "green-grid-pue")]
    if pue > T.PUE_HIGH:
        return [W("caution", "PUE_HIGH", "PUE unusually high",
                  f"PUE {pue:g} exceeds {T.PUE_HIGH:g}. Review facility efficiency.", "facility", "green-grid-pue")]
    return []


def environment_warnings(e: ModuleResult) -> list[W]:
    out: list[W] = []
    t = e.v("ambient_c")
    env = e.data["envelope_c"]
    cls = e.data["ashrae_class"]
    if t > env["allowable_max"] or t < env["allowable_min"]:
        out.append(W("critical", "TEMP_OUTSIDE_ALLOWABLE", "Temperature outside allowable envelope",
                     f"{t:.1f} °C is outside the {cls} allowable planning range "
                     f"({env['allowable_min']}–{env['allowable_max']} °C).", "environment", "ashrae-tc99-thermal"))
    elif t > env["recommended_max"] or t < env["recommended_min"]:
        out.append(W("caution", "TEMP_OUTSIDE_RECOMMENDED", "Temperature outside recommended envelope",
                     f"{t:.1f} °C is outside the recommended planning range ({env['recommended_min']}–"
                     f"{env['recommended_max']} °C). Equipment derating may apply.",
                     "environment", "ashrae-tc99-thermal"))
    if e.v("altitude_m") > T.ALTITUDE_DERATE_REVIEW_M:
        out.append(W("caution", "ALTITUDE_DERATE", "Altitude derating likely",
                     f"Site altitude {e.v('altitude_m'):,.0f} m exceeds {T.ALTITUDE_DERATE_REVIEW_M:,.0f} m. Enter "
                     "manufacturer derating factors for generators, cooling and IT equipment.",
                     "environment", "manufacturer-data"))
    return out


def rack_warnings(rc: ModuleResult) -> list[W]:
    planned = rc.get("racks_planned")
    if planned is not None and rc.v("racks_required") > planned:
        return [W("critical", "RACK_POWER_EXCEEDED", "Rack power rating exceeded",
                  f"Average rack load exceeds the provisioned rack rating: {rc.v('racks_required')} racks at "
                  f"{rc.v('rack_rating_kw'):g} kW are needed, {planned} are planned.", "rack")]
    return []


def capacity_warnings(balance: dict[str, Any]) -> list[W]:
    out: list[W] = []
    covered = {"ups", "transformer", "generator"}  # handled by dedicated rules above
    for row in balance["rows"]:
        if row["system"] in covered or row["status"] in ("ok", "not_configured"):
            continue
        sev = row["status"]
        out.append(W(sev, f"CAPACITY_{row['system'].upper()}",
                     f"{row['label']} capacity {'exceeded' if sev == 'critical' else 'near limit'}",
                     f"{row['label']} is loaded to {_pct(row['loading_pct'])} of usable capacity.", row["system"]))
    return out


SEVERITY_ORDER = {"critical": 0, "caution": 1, "info": 2}


def evaluate(modules: dict[str, ModuleResult], balance: dict[str, Any], targets: dict[str, float]) -> list[dict]:
    """Run every applicable rule and return warnings ordered by severity."""
    ws: list[W] = []
    ws += it_warnings(modules["it"])
    ws += facility_warnings(modules["facility"])
    ws += cooling_warnings(modules["cooling"])
    if "rack_count" in modules:
        ws += rack_warnings(modules["rack_count"])
    if "space" in modules:
        ws += density_warnings(modules["space"])
    if "circuit" in modules:
        ws += circuit_warnings(modules["circuit"])
    if "pdu" in modules:
        ws += pdu_warnings(modules["pdu"])
    if "ups" in modules:
        ws += ups_warnings(modules["ups"])
    if "battery" in modules:
        ws += battery_warnings(modules["battery"])
    if "transformer" in modules:
        ws += transformer_warnings(modules["transformer"], targets.get("transformer", 100))
    if "generator" in modules:
        ws += generator_warnings(modules["generator"], targets.get("generator", 100))
    if "bess" in modules:
        ws += bess_warnings(modules["bess"])
    if "environment" in modules:
        ws += environment_warnings(modules["environment"])
    ws += capacity_warnings(balance)
    return sort_warnings(ws)


def sort_warnings(ws: list[W]) -> list[dict]:
    return [w.to_dict() for w in sorted(ws, key=lambda w: SEVERITY_ORDER.get(w.severity, 9))]
