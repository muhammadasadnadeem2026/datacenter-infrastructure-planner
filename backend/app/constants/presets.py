"""Deployment presets. Each preset is a complete ProjectInputs document.

Selecting a preset fills every field; users may change any value afterwards.
"""

from __future__ import annotations

import copy
from typing import Any

_EXAMPLE_DEVICES = [
    {"equipment_type": "CPU Server", "description": "2U dual-socket compute", "quantity": 16,
     "nameplate_w": 800, "utilization_pct": 60, "rack": "R01"},
    {"equipment_type": "Storage", "description": "All-flash array", "quantity": 2,
     "nameplate_w": 1200, "utilization_pct": 70, "rack": "R02"},
    {"equipment_type": "Network Switch", "description": "Top-of-rack 48-port", "quantity": 4,
     "nameplate_w": 350, "utilization_pct": 50, "rack": "R01"},
    {"equipment_type": "Firewall", "description": "Edge firewall pair", "quantity": 2,
     "nameplate_w": 250, "utilization_pct": 50, "rack": "R02"},
]

BASE: dict[str, Any] = {
    "mode": "standard",
    "unit_system": "imperial",
    "preset": "enterprise",
    "it": {"input_mode": "rack_average", "rack_count": 20, "kw_per_rack": 11, "power_factor": 0.95,
           "utilization_pct": 100, "devices": _EXAMPLE_DEVICES},
    "rack": {"rack_rating_kw": 12},
    "space": {"room_area": 2000, "room_area_unit": "ft2"},
    "electrical": {"receptacle_id": "nema_l21_30", "voltage": 208, "current": 30, "phase": "three",
                   "continuous_derate": 0.8, "circuits_per_rack": 0},
    "pdu": {"voltage": 208, "amperage": 30, "phase": "three", "continuous_derate": 0.8,
            "growth_margin_pct": 20, "feed": "ab"},
    "ups": {"target_load_pct": 80, "redundancy": "N+1", "modules_n": 2, "module_kva": 0,
            "battery": {"enabled": False, "chemistry": "li_ion", "nominal_voltage": 480, "capacity_kwh": 40,
                        "capacity_ah": 0, "discharge_efficiency": 0.95, "degradation_pct": 20,
                        "runtime_target_min": 5}},
    "cooling": {"unit_capacity_kw": 100, "unit_count": 4, "redundancy": "N+1", "liquid_capture_pct": 0,
                "coolant_flow_lpm_per_kw": 0},
    "facility": {"pue": 1.5, "cooling_share_pct": None, "electrical_loss_share_pct": None, "other_share_pct": None},
    "environment": {"ambient_temp": 24, "ambient_temp_unit": "C", "altitude": 100, "altitude_unit": "m",
                    "ashrae_class": "A1", "humidity_pct": None, "temperature_derate_factor": 1.0,
                    "altitude_derate_factor": 1.0, "apply_derating": False},
    "utility": {"service_voltage_v": 13800, "service_capacity_kva": 1500},
    "transformer": {"enabled": True, "primary_voltage_v": 13800, "secondary_voltage_v": 480, "kva_rating": 750,
                    "efficiency": 0.985, "impedance_pct": 5.75, "quantity": 2, "redundancy": "N+1",
                    "target_utilization_pct": 80},
    "generator": {"enabled": True, "unit_kw": 500, "unit_kva": 625, "power_factor": 0.8, "quantity": 2,
                  "redundancy": "N+1", "step_load_pct": 50, "target_loading_pct": 80, "load_basis": "full",
                  "custom_load_kw": 0},
    "bess": {"enabled": False, "power_basis": "facility", "custom_power_mw": 1, "duration_min": 5,
             "dc_bus_voltage": 800, "pcs_efficiency": 0.97, "battery_efficiency": 0.95, "depth_of_discharge": 0.9,
             "eol_capacity_factor": 0.8, "redundancy": "N", "container_power_mw": 1, "container_energy_mwh": 2},
    "financial": {"electricity_rate": 0.13, "demand_charge": 0, "currency": "USD"},
    "advanced": {"hours_per_year": 8760, "facility_power_factor": None},
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


_OVERRIDES: dict[str, dict[str, Any]] = {
    "server_closet": {
        "mode": "quick",
        "it": {"rack_count": 1, "kw_per_rack": 2},
        "rack": {"rack_rating_kw": 3},
        "space": {"room_area": 100},
        "electrical": {"receptacle_id": "nema_5_20", "voltage": 120, "current": 20, "phase": "single"},
        "pdu": {"voltage": 120, "amperage": 20, "phase": "single", "feed": "none", "growth_margin_pct": 25},
        "ups": {"redundancy": "N", "modules_n": 1},
        "cooling": {"unit_capacity_kw": 3.5, "unit_count": 1, "redundancy": "N"},
        "facility": {"pue": 2.0},
        "utility": {"service_voltage_v": 208, "service_capacity_kva": 0},
        "transformer": {"enabled": False},
        "generator": {"enabled": False},
    },
    "enterprise": {},
    "colocation": {
        "mode": "engineering",
        "it": {"rack_count": 100, "kw_per_rack": 8},
        "rack": {"rack_rating_kw": 10},
        "space": {"room_area": 12000},
        "ups": {"redundancy": "2N", "modules_n": 2},
        "cooling": {"unit_capacity_kw": 300, "unit_count": 5, "redundancy": "N+1"},
        "facility": {"pue": 1.4},
        "utility": {"service_capacity_kva": 4000},
        "transformer": {"kva_rating": 2500, "quantity": 2, "redundancy": "2N"},
        "generator": {"unit_kw": 2000, "unit_kva": 2500, "quantity": 2, "redundancy": "N+1"},
    },
    "hpc": {
        "mode": "engineering",
        "it": {"rack_count": 12, "kw_per_rack": 30},
        "rack": {"rack_rating_kw": 35},
        "space": {"room_area": 1500},
        "electrical": {"receptacle_id": "iec_60309_32a_415", "voltage": 415, "current": 32, "phase": "three"},
        "pdu": {"voltage": 415, "amperage": 32, "phase": "three"},
        "cooling": {"unit_capacity_kw": 150, "unit_count": 4, "redundancy": "N+1"},
        "facility": {"pue": 1.3},
        "utility": {"service_capacity_kva": 2000},
        "transformer": {"kva_rating": 1000, "quantity": 2, "redundancy": "N+1", "secondary_voltage_v": 415},
        "generator": {"unit_kw": 750, "unit_kva": 938, "quantity": 2, "redundancy": "N+1"},
    },
    "ai_cluster": {
        "mode": "engineering",
        "it": {"rack_count": 8, "kw_per_rack": 120},
        "rack": {"rack_rating_kw": 132},
        "space": {"room_area": 1200},
        "electrical": {"receptacle_id": "iec_60309_63a_415", "voltage": 415, "current": 63, "phase": "three"},
        "pdu": {"voltage": 415, "amperage": 63, "phase": "three"},
        "ups": {"redundancy": "N+1", "modules_n": 3},
        "cooling": {"unit_capacity_kw": 500, "unit_count": 3, "redundancy": "N+1", "liquid_capture_pct": 80},
        "facility": {"pue": 1.25},
        "utility": {"service_capacity_kva": 4000},
        "transformer": {"kva_rating": 2500, "quantity": 2, "redundancy": "N+1", "secondary_voltage_v": 415},
        "generator": {"unit_kw": 1500, "unit_kva": 1875, "quantity": 2, "redundancy": "N+1"},
        "bess": {"enabled": True, "power_basis": "facility", "duration_min": 5, "container_power_mw": 1,
                 "container_energy_mwh": 2},
    },
    "edge": {
        "mode": "standard",
        "it": {"rack_count": 2, "kw_per_rack": 5},
        "rack": {"rack_rating_kw": 6},
        "space": {"room_area": 150},
        "electrical": {"receptacle_id": "nema_l6_30", "voltage": 208, "current": 30, "phase": "single"},
        "pdu": {"voltage": 208, "amperage": 30, "phase": "single"},
        "ups": {"redundancy": "N", "modules_n": 1},
        "cooling": {"unit_capacity_kw": 12, "unit_count": 2, "redundancy": "N+1"},
        "facility": {"pue": 1.6},
        "utility": {"service_voltage_v": 480, "service_capacity_kva": 0},
        "transformer": {"enabled": False},
        "generator": {"unit_kw": 30, "unit_kva": 37.5, "quantity": 1, "redundancy": "N"},
    },
    "custom": {},
}

PRESET_META: list[dict[str, str]] = [
    {"id": "server_closet", "name": "Server Closet", "summary": "1 rack · 2 kW/rack · 120 V · N"},
    {"id": "enterprise", "name": "Enterprise Data Center", "summary": "20 racks · 11 kW/rack · 480/208 V · N+1 UPS"},
    {"id": "colocation", "name": "Colocation Hall", "summary": "100 racks · 8 kW/rack · 2N UPS"},
    {"id": "hpc", "name": "High Density HPC", "summary": "12 racks · 30 kW/rack · three-phase"},
    {"id": "ai_cluster", "name": "AI / GPU Cluster", "summary": "8 racks · 120 kW/rack · liquid cooling"},
    {"id": "edge", "name": "Edge Data Center", "summary": "2 racks · 5 kW/rack · N UPS"},
    {"id": "custom", "name": "Custom", "summary": "Start from enterprise defaults"},
]


def get_preset(preset_id: str) -> dict[str, Any]:
    if preset_id not in _OVERRIDES:
        raise KeyError(preset_id)
    return _merge(BASE, {**_OVERRIDES[preset_id], "preset": preset_id})


def all_presets() -> list[dict[str, Any]]:
    return [{**meta, "inputs": get_preset(meta["id"])} for meta in PRESET_META]
