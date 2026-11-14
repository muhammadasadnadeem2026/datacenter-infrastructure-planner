"""Response models (drive the generated OpenAPI documentation)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.calculations.full import FullCalculation
from app.calculations.trace import ModuleResult
from app.version import CALC_ENGINE_VERSION


class StepOut(BaseModel):
    key: str
    label: str
    value: float | int | str | bool | None
    unit: str = ""
    formula: str = ""
    substitution: str = ""
    assumption: str = ""
    reference: str = ""


class ModuleOut(BaseModel):
    module: str
    steps: list[StepOut]
    data: dict[str, Any] = {}


class WarningOut(BaseModel):
    severity: str
    code: str
    title: str
    message: str
    affected_system: str
    reference: str = ""


class ToolResponse(BaseModel):
    engine_version: str
    modules: dict[str, ModuleOut]
    warnings: list[WarningOut]


class FullResponse(BaseModel):
    engine_version: str
    calculated_at: datetime
    mode: str
    unit_system: str
    modules: dict[str, ModuleOut]
    capacity: dict[str, Any]
    warnings: list[WarningOut]
    power_flow: dict[str, Any]
    sankey: dict[str, Any]
    summary: list[dict[str, Any]]


def tool_response(modules: dict[str, ModuleResult], warnings: list[dict]) -> dict[str, Any]:
    return {
        "engine_version": CALC_ENGINE_VERSION,
        "modules": {k: m.to_dict() for k, m in modules.items()},
        "warnings": warnings,
    }


def full_response(calc: FullCalculation) -> dict[str, Any]:
    return calc.to_dict()
