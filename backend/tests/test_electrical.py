import math

import pytest

from app.calculations import electrical as e


def test_kva_from_kw_spec_example():
    assert e.kva_from_kw(60, 0.95) == pytest.approx(63.1579, abs=1e-4)


def test_kw_from_kva_roundtrip():
    assert e.kw_from_kva(e.kva_from_kw(123.4, 0.9), 0.9) == pytest.approx(123.4)


def test_pf_one_is_valid():
    assert e.kva_from_kw(50, 1.0) == 50


@pytest.mark.parametrize("pf", [0, -0.5, 1.01, math.nan, math.inf])
def test_invalid_pf_rejected(pf):
    with pytest.raises(ValueError):
        e.kva_from_kw(10, pf)


def test_single_phase_208_30():
    kva = e.circuit_kva(208, 30, "single")
    assert kva == pytest.approx(6.24)
    assert e.usable_kva(kva, 0.8) == pytest.approx(4.992)


def test_three_phase_480_400():
    assert e.three_phase_kva(480, 400) == pytest.approx(332.55, abs=0.01)
    assert e.circuit_kva(480, 400, "three") == pytest.approx(math.sqrt(3) * 480 * 400 / 1000)


def test_min_circuits_spec_example():
    rack_kva = e.kva_from_kw(11, 0.95)
    assert rack_kva == pytest.approx(11.5789, abs=1e-4)
    assert e.min_circuits(rack_kva, 4.992) == 3


def test_min_circuits_exact_multiple_not_rounded_up():
    assert e.min_circuits(4.992 * 2, 4.992) == 2


def test_line_current():
    assert e.line_current(332.55, 480, "three") == pytest.approx(400, abs=0.01)
    assert e.line_current(6.24, 208, "single") == pytest.approx(30)


@pytest.mark.parametrize("v,a", [(0, 30), (208, 0), (-208, 30)])
def test_circuit_rejects_non_positive(v, a):
    with pytest.raises(ValueError):
        e.circuit_kva(v, a, "single")


def test_compute_circuit_spec_case():
    r = e.compute_circuit(voltage=208, current=30, phase="single", continuous_factor=0.8, rack_kw=11,
                          power_factor=0.95)
    assert r.v("nominal_kva") == pytest.approx(6.24)
    assert r.v("usable_kva") == pytest.approx(4.992)
    assert r.v("min_circuits") == 3
    assert r.v("installed_kva") == pytest.approx(14.976)
    # 11.5789 / (3 × 6.24) = 61.9 % of rating
    assert r.v("loading_pct") == pytest.approx(11.5789 / 18.72 * 100, abs=1e-3)
    assert r.v("status") == "ok"
    assert r.v("headroom_kva") == pytest.approx(14.976 - 11.5789, abs=1e-3)
    assert "ceil(" in r.steps["min_circuits"].substitution


def test_exact_80_percent_loading_is_caution_not_failure():
    # rack kVA = 0.8 × 6.24 = 4.992 kVA -> exactly 80 % of one 208 V / 30 A circuit
    r = e.compute_circuit(voltage=208, current=30, phase="single", continuous_factor=0.8, rack_kw=4.992,
                          power_factor=1.0, circuits_per_rack=1)
    assert r.v("loading_pct") == pytest.approx(80.0)
    assert r.v("status") == "caution"


def test_existing_circuit_overload_fails():
    r = e.compute_circuit(voltage=208, current=30, phase="single", continuous_factor=0.8, rack_kw=11,
                          power_factor=0.95, circuits_per_rack=2)
    assert r.v("loading_pct") == pytest.approx(11.5789 / 12.48 * 100, abs=1e-3)
    assert r.v("status") == "critical"


def test_status_bands():
    assert e.circuit_status(69.99) == "ok"
    assert e.circuit_status(70.0) == "ok"
    assert e.circuit_status(70.01) == "caution"
    assert e.circuit_status(80.0) == "caution"
    assert e.circuit_status(80.01) == "critical"


def test_status_scales_with_100pct_rated_breaker():
    assert e.circuit_status(95, continuous_factor=1.0) == "caution"
    assert e.circuit_status(85, continuous_factor=1.0) == "ok"


def test_power_conversion_both_directions():
    r = e.compute_power_conversion(kw=60, kva=None, power_factor=0.95)
    assert r.v("kva") == pytest.approx(63.1579, abs=1e-4)
    r = e.compute_power_conversion(kw=None, kva=100, power_factor=0.9)
    assert r.v("kw") == pytest.approx(90)


def test_describe_receptacle_derives_kva():
    rec = e.describe_receptacle({"voltage": 208, "amps": 30, "phase": "single", "continuous_derate": 0.8})
    assert rec["nominal_kva"] == pytest.approx(6.24)
    assert rec["usable_kva"] == pytest.approx(4.992)
