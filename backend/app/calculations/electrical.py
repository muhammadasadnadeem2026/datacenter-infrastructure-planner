"""Electrical fundamentals: power factor, circuit capacity, line current, circuit count."""

from __future__ import annotations

from app.calculations.trace import ModuleResult, cmp_round, fmt, require_positive, safe_ceil
from app.constants.thresholds import CIRCUIT_CAUTION_PCT, CIRCUIT_CRITICAL_PCT
from app.constants.units import SQRT3

# ---------------------------------------------------------------- pure functions


def kva_from_kw(kw: float, pf: float) -> float:
    require_positive("power factor", pf)
    if pf > 1:
        raise ValueError("power factor must be <= 1")
    return kw / pf


def kw_from_kva(kva: float, pf: float) -> float:
    if not 0 < pf <= 1:
        raise ValueError("power factor must be in (0, 1]")
    return kva * pf


def single_phase_kva(voltage: float, current: float) -> float:
    return voltage * current / 1000


def three_phase_kva(voltage: float, current: float) -> float:
    return SQRT3 * voltage * current / 1000


def circuit_kva(voltage: float, current: float, phase: str) -> float:
    require_positive("voltage", voltage)
    require_positive("current", current)
    return three_phase_kva(voltage, current) if phase == "three" else single_phase_kva(voltage, current)


def line_current(kva: float, voltage: float, phase: str) -> float:
    """Line current (A) for an apparent power at a line-to-line (3-ph) or line voltage (1-ph)."""
    require_positive("voltage", voltage)
    if phase == "three":
        return kva * 1000 / (SQRT3 * voltage)
    return kva * 1000 / voltage


def usable_kva(nominal_kva: float, continuous_factor: float) -> float:
    return nominal_kva * continuous_factor


def min_circuits(required_kva: float, usable_circuit_kva: float) -> int:
    require_positive("usable circuit kVA", usable_circuit_kva)
    return max(1, safe_ceil(required_kva / usable_circuit_kva))


def loading_pct(required: float, capacity: float) -> float:
    require_positive("capacity", capacity)
    return required / capacity * 100


def circuit_limits(continuous_factor: float = CIRCUIT_CRITICAL_PCT / 100) -> tuple[float, float]:
    """(caution %, critical %) of circuit rating. Default factor 0.80 gives the 70 / 80 % bands."""
    critical = continuous_factor * 100
    return critical * CIRCUIT_CAUTION_PCT / CIRCUIT_CRITICAL_PCT, critical


def circuit_status(loading: float, continuous_factor: float = CIRCUIT_CRITICAL_PCT / 100) -> str:
    caution, critical = circuit_limits(continuous_factor)
    val = cmp_round(loading)
    if val > cmp_round(critical):
        return "critical"
    if val > cmp_round(caution):
        return "caution"
    return "ok"


def kva_formula(phase: str) -> str:
    return "kVA = √3 × V × A / 1000" if phase == "three" else "kVA = V × A / 1000"


def kva_substitution(voltage: float, current: float, phase: str) -> str:
    prefix = "√3 × " if phase == "three" else ""
    return f"{prefix}{fmt(voltage)} × {fmt(current)} / 1000"


def current_formula(phase: str) -> str:
    return "I = kVA × 1000 / (√3 × V)" if phase == "three" else "I = kVA × 1000 / V"


def current_substitution(kva: float, voltage: float, phase: str) -> str:
    if phase == "three":
        return f"{fmt(kva)} × 1000 / (√3 × {fmt(voltage)})"
    return f"{fmt(kva)} × 1000 / {fmt(voltage)}"


def describe_receptacle(rec: dict) -> dict:
    nominal = circuit_kva(rec["voltage"], rec["amps"], rec["phase"])
    return {**rec, "nominal_kva": nominal, "usable_kva": usable_kva(nominal, rec["continuous_derate"])}


# ---------------------------------------------------------------- traced modules


def compute_power_conversion(*, kw: float | None, kva: float | None, power_factor: float) -> ModuleResult:
    """kW <-> kVA converter. Supply exactly one of kw / kva."""
    r = ModuleResult("power_factor")
    r.add("power_factor", "Power factor", power_factor, "", "Input", fmt(power_factor))
    if kw is not None:
        r.add("kw", "Real power", kw, "kW", "Input", fmt(kw))
        r.add("kva", "Apparent power", kva_from_kw(kw, power_factor), "kVA", "kVA = kW / PF",
              f"{fmt(kw)} / {fmt(power_factor)}")
    elif kva is not None:
        r.add("kva", "Apparent power", kva, "kVA", "Input", fmt(kva))
        r.add("kw", "Real power", kw_from_kva(kva, power_factor), "kW", "kW = kVA × PF",
              f"{fmt(kva)} × {fmt(power_factor)}")
    else:
        raise ValueError("either kw or kva is required")
    return r


def compute_circuit(
    *,
    voltage: float,
    current: float,
    phase: str,
    continuous_factor: float,
    rack_kw: float,
    power_factor: float,
    circuits_per_rack: int = 0,
    receptacle_name: str = "Custom",
) -> ModuleResult:
    r = ModuleResult("circuit")
    r.data["receptacle"] = receptacle_name
    r.data["phase"] = phase
    nominal = r.add("nominal_kva", "Nominal circuit capacity", circuit_kva(voltage, current, phase), "kVA",
                    kva_formula(phase), kva_substitution(voltage, current, phase),
                    assumption=f"{'Three' if phase == 'three' else 'Single'}-phase circuit, {receptacle_name}.")
    usable = r.add("usable_kva", "Usable continuous capacity", usable_kva(nominal, continuous_factor), "kVA",
                   "Usable kVA = Circuit kVA × continuous load factor",
                   f"{fmt(nominal)} × {fmt(continuous_factor)}",
                   assumption="Continuous load factor applied to the circuit rating.",
                   reference="nec-continuous-load")
    rack_kva = r.add("rack_kva", "Required rack apparent power", kva_from_kw(rack_kw, power_factor), "kVA",
                     "Rack kVA = Rack kW / PF", f"{fmt(rack_kw)} / {fmt(power_factor)}")
    n_min = r.add("min_circuits", "Minimum circuits per rack", min_circuits(rack_kva, usable), "circuits",
                  "N = ceil(Rack kVA / Usable circuit kVA)", f"ceil({fmt(rack_kva)} / {fmt(usable)})",
                  assumption="Load shared across circuits of one feed; A/B redundancy doubles the count (see PDU).")
    existing = circuits_per_rack > 0
    n_eval = circuits_per_rack if existing else n_min
    r.data["evaluated_on"] = "existing" if existing else "minimum"
    installed = r.add("installed_kva", "Installed usable circuit capacity per rack", usable * n_eval, "kVA",
                      "Installed = Usable circuit kVA × circuits", f"{fmt(usable)} × {n_eval}",
                      assumption=("Existing circuits entered by user." if existing
                                  else "Evaluated at the minimum circuit count."))
    rated = r.add("installed_nominal_kva", "Installed nominal circuit capacity per rack", nominal * n_eval, "kVA",
                  "Nominal installed = Circuit kVA × circuits", f"{fmt(nominal)} × {n_eval}")
    load = r.add("loading_pct", "Circuit loading (of rating)", loading_pct(rack_kva, rated), "%",
                 "Loading % = Rack kVA / Nominal installed kVA × 100", f"{fmt(rack_kva)} / {fmt(rated)} × 100",
                 assumption=(f"Compared with the circuit rating; loading above {fmt(continuous_factor * 100)} % of "
                             "rating fails the continuous-load check."),
                 reference="nec-continuous-load")
    r.add("loading_of_usable_pct", "Circuit loading (of usable capacity)", loading_pct(rack_kva, installed), "%",
          "Loading % = Rack kVA / Usable installed kVA × 100", f"{fmt(rack_kva)} / {fmt(installed)} × 100")
    r.add("headroom_kva", "Remaining headroom", installed - rack_kva, "kVA",
          "Headroom = Installed capacity − Rack kVA", f"{fmt(installed)} − {fmt(rack_kva)}")
    r.add("circuit_current_a", "Rack current per circuit", line_current(rack_kva / n_eval, voltage, phase), "A",
          current_formula(phase), current_substitution(rack_kva / n_eval, voltage, phase),
          assumption="Balanced load across circuits (and phases for three-phase).")
    caution, critical = circuit_limits(continuous_factor)
    r.add("status", "Circuit loading status", circuit_status(load, continuous_factor), "",
          f"≤{fmt(caution)} % normal; ≤{fmt(critical)} % caution; >{fmt(critical)} % fails continuous-load check",
          f"{fmt(load)} %")
    r.data["circuits_per_rack"] = circuits_per_rack
    r.data["limits_pct"] = {"caution": caution, "critical": critical}
    return r
