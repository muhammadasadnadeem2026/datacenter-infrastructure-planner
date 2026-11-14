"""Cooling-density classification bands.

Bands are (min_kw, max_kw] per rack: a rack at exactly 5 kW is 'conventional',
5.01 kW is 'containment'. The last band has no upper bound.
All descriptive text lives here, not in UI components.
"""

COOLING_CLASSES: list[dict] = [
    {
        "id": "conventional",
        "min_kw": 0.0,
        "max_kw": 5.0,
        "name": "Conventional air cooling",
        "description": "Conventional perimeter CRAC/CRAH cooling is typically adequate at this density.",
        "severity": "info",
    },
    {
        "id": "containment",
        "min_kw": 5.0,
        "max_kw": 12.0,
        "name": "Air cooling with containment",
        "description": "Hot- or cold-aisle containment is recommended to prevent bypass and recirculation.",
        "severity": "info",
    },
    {
        "id": "high_density_air",
        "min_kw": 12.0,
        "max_kw": 20.0,
        "name": "High-density air cooling",
        "description": "High-density air cooling (close-coupled in-row units, full containment) should be planned.",
        "severity": "info",
    },
    {
        "id": "hybrid",
        "min_kw": 20.0,
        "max_kw": 50.0,
        "name": "Rear-door / hybrid cooling",
        "description": "Rear-door heat exchangers or hybrid air/liquid cooling should be evaluated.",
        "severity": "caution",
    },
    {
        "id": "liquid",
        "min_kw": 50.0,
        "max_kw": None,
        "name": "Direct-to-chip liquid cooling",
        "description": "Direct-to-chip or other liquid cooling should be evaluated; air cooling alone is unlikely to be practical.",
        "severity": "caution",
    },
]

# Thermal (heat-density) tiers shown by the rack-density tool.
THERMAL_TIERS: list[dict] = [
    {"id": "low", "min_kw": 0.0, "max_kw": 5.0, "name": "Low density"},
    {"id": "medium", "min_kw": 5.0, "max_kw": 15.0, "name": "Medium density"},
    {"id": "high", "min_kw": 15.0, "max_kw": 30.0, "name": "High density"},
    {"id": "very_high", "min_kw": 30.0, "max_kw": 80.0, "name": "Very high density"},
    {"id": "extreme", "min_kw": 80.0, "max_kw": None, "name": "Extreme density (AI / liquid)"},
]
