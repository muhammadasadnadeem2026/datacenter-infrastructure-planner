import pytest

from app.calculations import cooling, energy, facility


def test_cooling_spec_values():
    r = cooling.compute_cooling(it_kw=60, rack_count=10)
    assert r.v("thermal_kw") == 60
    assert r.v("btu_hr") == pytest.approx(204_728.52)
    assert r.v("tons") == pytest.approx(17.0607, abs=1e-4)
    assert r.v("btu_hr_per_rack") == pytest.approx(20_472.852)
    assert r.v("tons_per_rack") == pytest.approx(1.70607, abs=1e-5)


@pytest.mark.parametrize("kw,cls", [
    (0.5, "conventional"), (5.0, "conventional"), (5.01, "containment"), (12, "containment"),
    (12.5, "high_density_air"), (20, "high_density_air"), (30, "hybrid"), (50, "hybrid"),
    (50.1, "liquid"), (150, "liquid"),
])
def test_cooling_classification_bands(kw, cls):
    assert cooling.classify_cooling(kw)["id"] == cls


def test_cooling_installed_capacity_with_redundancy():
    r = cooling.compute_cooling(it_kw=220, rack_count=20, unit_capacity_kw=100, unit_count=4, redundancy="N+1")
    assert r.v("installed_kw") == 400
    assert r.v("usable_kw") == 300


def test_cooling_derate_factor_applied():
    r = cooling.compute_cooling(it_kw=100, rack_count=10, unit_capacity_kw=100, unit_count=2, redundancy="N",
                                capacity_factor=0.9)
    assert r.v("usable_kw") == pytest.approx(180)


def test_facility_pue():
    r = facility.compute_facility(it_kw=60, pue=1.5, power_factor=0.95)
    assert r.v("facility_kw") == 90
    assert r.v("overhead_kw") == 30
    assert r.v("it_pct") == pytest.approx(66.6667, abs=1e-4)
    assert r.v("overhead_pct") == pytest.approx(33.3333, abs=1e-4)
    assert r.data["breakdown"][1]["label"] == "Facility Overhead"
    assert r.data["split_given"] is False


def test_facility_split_labels_unallocated():
    r = facility.compute_facility(it_kw=100, pue=1.5, power_factor=1, cooling_share_pct=60,
                                  electrical_loss_share_pct=20)
    assert r.v("cooling_kw") == pytest.approx(30)
    assert r.v("electrical_losses_kw") == pytest.approx(10)
    assert r.v("unallocated_kw") == pytest.approx(10)


def test_pue_below_one_rejected():
    with pytest.raises(ValueError):
        facility.facility_kw(100, 0.9)


def test_annual_energy_and_cost_spec():
    r = energy.compute_energy(it_kw=60, facility_kw=90, electricity_rate=0.13)
    assert r.v("annual_it_kwh") == pytest.approx(525_600)
    assert r.v("annual_facility_kwh") == pytest.approx(788_400)
    assert r.v("annual_energy_cost") == pytest.approx(102_492)
    assert r.v("annual_cost") == pytest.approx(102_492)
    assert r.v("monthly_cost") == pytest.approx(8_541)


def test_demand_charge():
    r = energy.compute_energy(it_kw=60, facility_kw=90, electricity_rate=0.13, demand_charge=15)
    assert r.v("annual_demand_cost") == pytest.approx(90 * 15 * 12)
    assert r.v("annual_cost") == pytest.approx(102_492 + 16_200)
    assert "estimate" in r.steps["annual_cost"].assumption.lower()


def test_utilization_reduces_energy_only():
    r = energy.compute_energy(it_kw=100, facility_kw=150, electricity_rate=0.1, utilization_pct=50)
    assert r.v("annual_facility_kwh") == pytest.approx(75 * 8760)
    assert r.v("annual_demand_cost") == 0


def test_liquid_cooling_split_and_flow():
    r = cooling.compute_cooling(it_kw=1000, rack_count=8, liquid_capture_pct=85, coolant_flow_lpm_per_kw=1.5)
    assert r.v("liquid_heat_kw") == pytest.approx(850)
    assert r.v("air_heat_kw") == pytest.approx(150)
    assert r.v("air_tons") == pytest.approx(150 * 3412.142 / 12000)
    assert r.v("coolant_flow_lpm") == pytest.approx(1500)
    assert r.v("coolant_flow_gpm") == pytest.approx(1500 / 3.785411784)
    assert r.v("coolant_flow_lpm_per_rack") == pytest.approx(187.5)


def test_no_liquid_split_by_default():
    r = cooling.compute_cooling(it_kw=100, rack_count=10)
    assert "liquid_heat_kw" not in r.steps
    with pytest.raises(ValueError):
        cooling.liquid_heat_kw(100, 1.2)
