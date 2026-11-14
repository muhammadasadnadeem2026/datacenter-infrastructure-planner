import math

import pytest

from app.calculations import bess, generator, transformer


def test_transformer_fla_and_fault():
    fla = transformer.full_load_current(2500, 480)
    assert fla == pytest.approx(2500 * 1000 / (math.sqrt(3) * 480))
    assert fla == pytest.approx(3007.03, abs=0.01)
    assert transformer.terminal_fault_current(fla, 5.75) == pytest.approx(fla / 0.0575)


def test_transformer_loading_with_redundancy():
    r = transformer.compute_transformer(required_kva=2000, primary_voltage=13800, secondary_voltage=480,
                                        kva_rating=2500, efficiency=0.99, impedance_pct=5.75, quantity=2,
                                        redundancy="N+1", target_utilization_pct=80)
    assert r.v("installed_kva") == 5000
    assert r.v("usable_kva") == 2500
    assert r.v("loading_pct") == pytest.approx(80)
    assert r.v("loading_installed_pct") == pytest.approx(40)
    assert r.v("units_required_n") == 1
    assert r.v("units_recommended") == 2
    assert r.v("input_kva") == pytest.approx(2000 / 0.99)
    assert "short-circuit" in r.steps["fault_current_a"].assumption


def test_transformer_overload():
    r = transformer.compute_transformer(required_kva=3000, primary_voltage=13800, secondary_voltage=480,
                                        kva_rating=2500, efficiency=0.99, impedance_pct=5.75, quantity=2,
                                        redundancy="N+1", target_utilization_pct=80)
    assert r.v("loading_pct") == pytest.approx(120)


def test_generator_sizing():
    r = generator.compute_generator(critical_load_kw=3000, load_basis="full", unit_kw=2000, unit_kva=2500,
                                    power_factor=0.8, quantity=3, redundancy="N+1", step_load_pct=50,
                                    target_loading_pct=80)
    assert r.v("unit_usable_kw") == 2000
    assert r.v("required_capacity_kw") == pytest.approx(3750)
    assert r.v("units_required_n") == 2
    assert r.v("units_recommended") == 3
    assert r.v("usable_kw") == 4000
    assert r.v("loading_pct") == pytest.approx(75)
    assert r.v("capacity_ok") is True
    assert r.v("reserve_kw") == 1000


def test_generator_kva_limited():
    # kVA × PF lower than kW rating -> kVA limits
    assert generator.unit_usable_kw(2000, 2000, 0.8) == 1600


def test_generator_insufficient():
    r = generator.compute_generator(critical_load_kw=5000, load_basis="full", unit_kw=2000, unit_kva=2500,
                                    power_factor=0.8, quantity=3, redundancy="N+1", step_load_pct=50,
                                    target_loading_pct=80)
    assert r.v("capacity_ok") is False


def test_bess_spec_formulas():
    r = bess.compute_bess(power_mw=10, power_basis_note="", duration_min=15, dc_bus_voltage=1000,
                          pcs_efficiency=0.97, battery_efficiency=0.95, depth_of_discharge=0.9,
                          eol_capacity_factor=0.8, redundancy="N", container_power_mw=2.5, container_energy_mwh=5)
    e_load = 10 * 0.25
    e_batt = e_load / (0.97 * 0.95 * 0.9 * 0.8)
    assert r.v("load_mwh") == pytest.approx(2.5)
    assert r.v("battery_mwh") == pytest.approx(e_batt)
    assert r.v("containers_power") == 4
    assert r.v("containers_energy") == math.ceil(e_batt / 5)
    assert r.v("containers_required") == 4
    assert r.v("sizing_driver") == "power"
    assert r.v("installed_mw") == 10
    assert r.v("dc_power_mw") == pytest.approx(10 / 0.97)
    assert r.v("dc_current_a") == pytest.approx(10 / 0.97 * 1e6 / 1000)


def test_bess_mw_scale_energy_driven_with_redundancy():
    r = bess.compute_bess(power_mw=50, power_basis_note="", duration_min=120, dc_bus_voltage=1500,
                          pcs_efficiency=0.97, battery_efficiency=0.95, depth_of_discharge=0.9,
                          eol_capacity_factor=0.8, redundancy="N+1", container_power_mw=2.5, container_energy_mwh=5)
    e_batt = 100 / (0.97 * 0.95 * 0.9 * 0.8)
    n_e = math.ceil(e_batt / 5)
    assert r.v("containers_energy") == n_e
    assert r.v("sizing_driver") == "energy"
    assert r.v("containers_total") == n_e + 1
    assert r.v("installed_mwh") == (n_e + 1) * 5
    assert r.v("energy_margin_pct") > 0


@pytest.mark.parametrize("field", ["pcs_efficiency", "battery_efficiency", "dod", "eol_factor"])
def test_bess_rejects_zero_factors(field):
    kw = dict(load_mwh=1, pcs_efficiency=0.97, battery_efficiency=0.95, dod=0.9, eol_factor=0.8)
    kw[field] = 0
    with pytest.raises(ValueError):
        bess.battery_energy_required_mwh(**kw)
