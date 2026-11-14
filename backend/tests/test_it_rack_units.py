import pytest

from app.calculations import it_load, rack_count, rack_density, units
from app.schemas.inputs import Device


def test_rack_average():
    r = it_load.compute_it_load(input_mode="rack_average", rack_count=10, kw_per_rack=6, power_factor=0.95)
    assert r.v("it_kw") == 60
    assert r.v("it_kva") == pytest.approx(63.1579, abs=1e-4)
    assert r.v("kw_per_rack") == 6
    assert r.steps["it_kw"].substitution == "10 × 6"


def test_device_list():
    devices = [
        Device(equipment_type="GPU Server", quantity=4, nameplate_w=10_000, utilization_pct=80, rack="A"),
        Device(equipment_type="Network Switch", quantity=2, nameplate_w=500, utilization_pct=50, rack="A"),
        Device(equipment_type="Storage", quantity=1, nameplate_w=2000, utilization_pct=100, rack="B"),
    ]
    r = it_load.compute_it_load(input_mode="device_list", rack_count=2, kw_per_rack=1, power_factor=0.95,
                                devices=devices)
    assert r.v("device_total_w") == pytest.approx(32_000 + 500 + 2_000)
    assert r.v("it_kw") == pytest.approx(34.5)
    assert r.v("kw_per_rack") == pytest.approx(17.25)
    summary = {x["rack"]: x["kw"] for x in r.data["rack_summary"]}
    assert summary == {"A": pytest.approx(32.5), "B": pytest.approx(2.0)}


def test_zero_racks_invalid():
    with pytest.raises(ValueError):
        it_load.per_rack_kw(10, 0)


def test_area_density():
    r = rack_density.compute_space(it_kw=60, rack_count=10, area_value=1000, area_unit="ft2")
    assert r.v("w_per_ft2") == pytest.approx(60)
    assert r.v("area_m2") == pytest.approx(92.90304)
    assert r.v("w_per_m2") == pytest.approx(60_000 / 92.90304)


def test_area_density_metric_input():
    r = rack_density.compute_space(it_kw=100, rack_count=10, area_value=100, area_unit="m2")
    assert r.v("w_per_m2") == pytest.approx(1000)
    assert r.v("area_ft2") == pytest.approx(1076.391, abs=1e-3)


def test_rack_count_spec_example():
    r = rack_count.compute_rack_count(it_kw=8400, rack_power_kw=142)
    assert r.v("racks_required") == 60
    assert r.v("installed_rack_kw") == 8520
    assert r.v("unused_kw") == 120


def test_rack_density_tool_composes_modules():
    out = rack_density.compute_rack_density(rack_count=8, kw_per_rack=120, area_value=1200, area_unit="ft2",
                                            voltage=415, current=63, phase="three", continuous_factor=0.8,
                                            power_factor=0.95)
    assert out["rack_density"].v("it_kw") == 960
    assert out["rack_density"].data["cooling_class"]["id"] == "liquid"
    assert out["rack_density"].data["thermal_class"]["id"] == "extreme"
    assert out["circuit"].v("min_circuits") == 4
    assert out["space"].v("w_per_ft2") == pytest.approx(800)


@pytest.mark.parametrize("cid,value,expected", [
    ("f_to_c", 212, 100), ("c_to_f", 0, 32), ("ft2_to_m2", 1, 0.09290304), ("m2_to_ft2", 0.09290304, 1),
    ("kw_to_mw", 1500, 1.5), ("mw_to_kw", 2, 2000), ("kw_to_btu_hr", 1, 3412.142),
    ("btu_hr_to_kw", 3412.142, 1), ("btu_hr_to_tons", 12000, 1), ("tons_to_btu_hr", 2, 24000),
])
def test_conversions(cid, value, expected):
    assert units.convert(cid, value).v("result") == pytest.approx(expected)


def test_conversion_with_params():
    assert units.convert("amps_to_kva", 400, voltage=480, phase="three").v("result") == pytest.approx(332.55, abs=0.01)
    assert units.convert("kva_to_amps", 6.24, voltage=208, phase="single").v("result") == pytest.approx(30)
    assert units.convert("kw_to_kva", 60, power_factor=0.95).v("result") == pytest.approx(63.1579, abs=1e-4)


def test_conversion_missing_param():
    with pytest.raises(ValueError):
        units.convert("amps_to_kva", 400)
    with pytest.raises(ValueError):
        units.convert("nope", 1)
