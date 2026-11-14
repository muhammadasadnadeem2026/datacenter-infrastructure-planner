"""Receptacle / rack-power connection library.

Editable records. Nominal and usable kVA are NOT stored here; they are derived by
app.calculations.electrical.describe_receptacle so the formula exists only once.
continuous_derate is a project assumption (0.80 reflects the common North American
continuous-load practice); edit it for other jurisdictions.
"""

RECEPTACLES: list[dict] = [
    {"id": "nema_5_20", "name": "NEMA 5-20", "voltage": 120, "amps": 20, "phase": "single",
     "continuous_derate": 0.80, "description": "120 V 20 A straight-blade; small closets and edge racks."},
    {"id": "nema_l5_20", "name": "NEMA L5-20", "voltage": 120, "amps": 20, "phase": "single",
     "continuous_derate": 0.80, "description": "120 V 20 A locking; low-density racks."},
    {"id": "nema_l6_20", "name": "NEMA L6-20", "voltage": 208, "amps": 20, "phase": "single",
     "continuous_derate": 0.80, "description": "208 V 20 A single-phase locking."},
    {"id": "nema_l6_30", "name": "NEMA L6-30", "voltage": 208, "amps": 30, "phase": "single",
     "continuous_derate": 0.80, "description": "208 V 30 A single-phase locking; common enterprise rack feed."},
    {"id": "nema_l21_30", "name": "NEMA L21-30 (208 V three-phase)", "voltage": 208, "amps": 30, "phase": "three",
     "continuous_derate": 0.80, "description": "120/208 V 30 A three-phase wye locking."},
    {"id": "iec_60309_60a_208", "name": "IEC 60309 60 A (208 V three-phase)", "voltage": 208, "amps": 60,
     "phase": "three", "continuous_derate": 0.80, "description": "208 V 60 A three-phase pin-and-sleeve; high-density racks."},
    {"id": "iec_60309_32a_415", "name": "IEC 60309 32 A (415/240 V three-phase)", "voltage": 415, "amps": 32,
     "phase": "three", "continuous_derate": 0.80, "description": "415/240 V 32 A three-phase wye pin-and-sleeve."},
    {"id": "iec_60309_63a_415", "name": "IEC 60309 63 A (415/240 V three-phase)", "voltage": 415, "amps": 63,
     "phase": "three", "continuous_derate": 0.80, "description": "415/240 V 63 A three-phase; AI / HPC racks."},
    {"id": "nema_l16_30_480", "name": "NEMA L16-30 (480 V three-phase)", "voltage": 480, "amps": 30,
     "phase": "three", "continuous_derate": 0.80, "description": "480 V 30 A three-phase delta locking."},
    {"id": "iec_c13", "name": "IEC C13 (equipment inlet)", "voltage": 208, "amps": 10, "phase": "single",
     "continuous_derate": 0.80, "description": "Equipment-side connector (10 A IEC rating; 15 A in some listings). Not a branch circuit."},
    {"id": "iec_c19", "name": "IEC C19 (equipment inlet)", "voltage": 208, "amps": 16, "phase": "single",
     "continuous_derate": 0.80, "description": "Equipment-side connector (16 A IEC rating; 20 A in some listings). Not a branch circuit."},
]

CUSTOM_RECEPTACLE_ID = "custom"


def get_receptacle(receptacle_id: str) -> dict | None:
    for rec in RECEPTACLES:
        if rec["id"] == receptacle_id:
            return rec
    return None
