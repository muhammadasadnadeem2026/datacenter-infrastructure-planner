"""Reference data endpoints (library records, classifications, presets)."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.calculations.electrical import describe_receptacle
from app.calculations.environment import ASHRAE_ENVELOPES_C
from app.calculations.redundancy import REDUNDANCY_OPTIONS
from app.calculations.units import list_conversions
from app.constants import thresholds
from app.constants.ai_racks import AI_RACK_CLASSES, load_equipment_references
from app.constants.cooling import COOLING_CLASSES, THERMAL_TIERS
from app.constants.disclaimer import DISCLAIMER
from app.constants.presets import all_presets
from app.constants.receptacles import RECEPTACLES
from app.constants.voltage_levels import VOLTAGE_LEVELS
from app.version import APP_NAME, CALC_ENGINE_VERSION

router = APIRouter(prefix="/api/constants", tags=["constants"])
meta_router = APIRouter(prefix="/api", tags=["meta"])

_REFS = Path(__file__).resolve().parents[1] / "constants" / "references.json"


@router.get("/receptacles")
def receptacles():
    return [describe_receptacle(r) for r in RECEPTACLES]


@router.get("/cooling-classes")
def cooling_classes():
    return {"cooling_classes": COOLING_CLASSES, "thermal_tiers": THERMAL_TIERS}


@router.get("/voltage-levels")
def voltage_levels():
    return VOLTAGE_LEVELS


@router.get("/presets")
def presets():
    return all_presets()


@router.get("/references")
def references():
    return json.loads(_REFS.read_text(encoding="utf-8"))


@router.get("/ai-racks")
def ai_racks():
    return {"classes": AI_RACK_CLASSES, "equipment_references": load_equipment_references()}


@router.get("/conversions")
def conversions():
    return list_conversions()


@router.get("/thresholds")
def get_thresholds():
    return {k: v for k, v in vars(thresholds).items() if k.isupper()}


@router.get("/environment")
def environment_envelopes():
    return {"ashrae_envelopes_c": ASHRAE_ENVELOPES_C}


@meta_router.get("/meta")
def meta():
    return {
        "app": APP_NAME,
        "engine_version": CALC_ENGINE_VERSION,
        "disclaimer": DISCLAIMER,
        "redundancy_options": list(REDUNDANCY_OPTIONS),
    }


@meta_router.get("/health")
def health():
    return {"status": "ok"}
