"""AI / GPU rack classes and equipment references.

The calculation engine only ever consumes a rack power value (kW). Vendor platform
records are reference data with a review date; they are never used inside formulas.
Equipment references are loaded from equipment_references.json so they can be edited
without code changes.
"""

import json
from pathlib import Path

AI_RACK_CLASSES: list[dict] = [
    {"id": "enterprise", "name": "Traditional Enterprise Rack", "min_kw": 10, "max_kw": 15, "typical_kw": 12,
     "cooling_type": "Air (containment)"},
    {"id": "gpu_hpc", "name": "GPU / HPC Rack", "min_kw": 30, "max_kw": 50, "typical_kw": 40,
     "cooling_type": "Air + rear-door / hybrid"},
    {"id": "ai_high_density", "name": "High Density AI Rack", "min_kw": 80, "max_kw": 150, "typical_kw": 120,
     "cooling_type": "Direct-to-chip liquid"},
    {"id": "next_gen_liquid", "name": "Next-generation liquid-cooled rack", "min_kw": 150, "max_kw": None,
     "typical_kw": 200, "cooling_type": "Direct-to-chip / immersion liquid"},
]

_REF_FILE = Path(__file__).with_name("equipment_references.json")
_LOCAL_REF_FILE = Path(__file__).with_name("equipment_references.local.json")
"""Optional and git-ignored: vendor data received under NDA, so it never enters the repository."""


def load_equipment_references() -> list[dict]:
    refs = json.loads(_REF_FILE.read_text(encoding="utf-8"))
    if _LOCAL_REF_FILE.exists():
        refs += json.loads(_LOCAL_REF_FILE.read_text(encoding="utf-8"))
    return refs
