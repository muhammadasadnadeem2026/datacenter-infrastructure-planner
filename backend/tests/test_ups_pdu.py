import pytest

from app.calculations import pdu, ups
from app.calculations.redundancy import installed_unit_count, redundancy_multiplier, usable_units


def test_redundancy_multiplier():
    assert redundancy_multiplier("N", 3) == 1.0
    assert redundancy_multiplier("N+1", 2) == 1.5
    assert redundancy_multiplier("N+1", 4) == 1.25
    assert redundancy_multiplier("2N", 2) == 2.0
    with pytest.raises(ValueError):
        redundancy_multiplier("N+1", 0)


def test_unit_counts():
    assert installed_unit_count("N+1", 3) == 4
    assert installed_unit_count("2N", 2) == 4
    assert usable_units(4, "N+1") == 3
    assert usable_units(4, "2N") == 2
    assert usable_units(1, "N+1") == 0


def test_ups_auto_sizing_n_plus_1():
    r = ups.compute_ups(load_kw=60, power_factor=0.95, target_load_pct=80, redundancy="N+1", modules_n=2)
    load = 60 / 0.95
    assert r.v("load_kva") == pytest.approx(load)
    assert r.v("required_kva") == pytest.approx(load / 0.8)
    assert r.v("redundancy_multiplier") == 1.5
    assert r.v("installed_kva") == pytest.approx(load / 0.8 * 1.5)
    assert r.v("module_count") == 3
    assert r.v("module_kva") == pytest.approx(load / 0.8 / 2)
    assert r.v("utilization_usable_pct") == pytest.approx(80)
    assert r.v("utilization_installed_pct") == pytest.approx(80 / 1.5)


def test_ups_2n():
    r = ups.compute_ups(load_kw=100, power_factor=1, target_load_pct=100, redundancy="2N", modules_n=1)
    assert r.v("installed_kva") == 200
    assert r.v("module_count") == 2
    assert r.v("utilization_installed_pct") == pytest.approx(50)


def test_ups_fixed_module_size_flags_short():
    r = ups.compute_ups(load_kw=500, power_factor=1, target_load_pct=80, redundancy="N+1", modules_n=2,
                        module_kva=250)
    assert r.v("modules_required_n") == 3  # 625 / 250
    assert r.v("installed_kva") == 750
    assert r.v("utilization_usable_pct") == pytest.approx(100)


def test_ups_target_invalid():
    with pytest.raises(ValueError):
        ups.required_ups_kva(100, 0)


def test_battery_runtime_requires_capacity():
    with pytest.raises(ValueError):
        ups.compute_battery(load_kw=100, chemistry="li_ion", nominal_voltage=480, capacity_kwh=0, capacity_ah=0,
                            discharge_efficiency=0.95, degradation_pct=20, runtime_target_min=5)


def test_battery_runtime_idealized():
    r = ups.compute_battery(load_kw=100, chemistry="li_ion", nominal_voltage=480, capacity_kwh=20, capacity_ah=0,
                            discharge_efficiency=0.95, degradation_pct=20, runtime_target_min=5)
    assert r.v("available_kwh") == pytest.approx(20 * 0.8 * 0.95)
    assert r.v("runtime_min") == pytest.approx(15.2 / 100 * 60)
    assert "manufacturer" in r.steps["runtime_min"].assumption.lower()


def test_battery_from_ah():
    r = ups.compute_battery(load_kw=10, chemistry="vrla", nominal_voltage=480, capacity_kwh=0, capacity_ah=100,
                            discharge_efficiency=1, degradation_pct=0, runtime_target_min=5)
    assert r.v("nameplate_kwh") == pytest.approx(48)


def test_pdu_ab_three_phase():
    r = pdu.compute_pdu(rack_kw=11, power_factor=0.95, growth_margin_pct=20, voltage=208, amperage=30,
                        phase="three", continuous_factor=0.8, feed="ab")
    design_kva = 11 * 1.2 / 0.95
    rated = 3 ** 0.5 * 208 * 30 / 1000
    assert r.v("design_kw") == pytest.approx(13.2)
    assert r.v("rack_kva") == pytest.approx(design_kva)
    assert r.v("pdu_kva") == pytest.approx(rated)
    assert r.v("pdus_per_feed") == 2
    assert r.v("pdus_total") == 4
    assert r.v("load_per_pdu_failover_kva") == pytest.approx(design_kva / 2)
    assert r.v("loading_pct") == pytest.approx(design_kva / 2 / rated * 100)
    assert r.v("line_current_a") == pytest.approx(design_kva / 2 * 1000 / (3 ** 0.5 * 208))
    assert r.v("kva_per_phase") == pytest.approx(design_kva / 2 / 3)


def test_pdu_single_feed():
    r = pdu.compute_pdu(rack_kw=2, power_factor=1, growth_margin_pct=0, voltage=120, amperage=20, phase="single",
                        continuous_factor=0.8, feed="none")
    assert r.v("pdus_total") == 2  # 2 kVA > 1.92 usable
    assert "kva_per_phase" not in r.steps
