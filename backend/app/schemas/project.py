from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.inputs import ProjectInputs


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    inputs: ProjectInputs


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    inputs: ProjectInputs | None = None


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    calculator_version: str


class ProjectOut(ProjectSummary):
    inputs: dict[str, Any]
    results: dict[str, Any]
    warnings: list[dict[str, Any]]
