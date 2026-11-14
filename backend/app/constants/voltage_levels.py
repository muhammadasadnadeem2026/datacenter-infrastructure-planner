"""Common data-center distribution voltage levels (line-to-line)."""

VOLTAGE_LEVELS: list[dict] = [
    {"id": "34500", "voltage_v": 34500, "label": "34.5 kV", "class": "MV", "typical_use": "Utility / campus substation feeders"},
    {"id": "13800", "voltage_v": 13800, "label": "13.8 kV", "class": "MV", "typical_use": "Utility service, MV distribution"},
    {"id": "12470", "voltage_v": 12470, "label": "12.47 kV", "class": "MV", "typical_use": "Utility distribution service"},
    {"id": "4160", "voltage_v": 4160, "label": "4.16 kV", "class": "MV", "typical_use": "Large motors, chiller plants"},
    {"id": "480", "voltage_v": 480, "label": "480 V", "class": "LV", "typical_use": "LV switchgear, UPS input, mechanical loads"},
    {"id": "415", "voltage_v": 415, "label": "415 V", "class": "LV", "typical_use": "415/240 V distribution to racks"},
    {"id": "208", "voltage_v": 208, "label": "208 V", "class": "LV", "typical_use": "120/208 V distribution to racks"},
]
