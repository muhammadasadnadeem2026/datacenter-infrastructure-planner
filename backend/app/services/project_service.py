"""Project persistence. Results are always recomputed server-side on save."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculations.full import run_full_calculation
from app.models.project import Project
from app.schemas.inputs import ProjectInputs


def _apply_calc(project: Project, inputs: ProjectInputs) -> None:
    calc = run_full_calculation(inputs).to_dict()
    project.inputs = inputs.model_dump(mode="json")
    project.results = calc
    project.warnings = calc["warnings"]
    project.calculator_version = calc["engine_version"]


def list_projects(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.updated_at.desc())))


def get_project(db: Session, project_id: str) -> Project | None:
    return db.get(Project, project_id)


def create_project(db: Session, name: str, inputs: ProjectInputs) -> Project:
    project = Project(name=name)
    _apply_calc(project, inputs)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project: Project, name: str | None, inputs: ProjectInputs | None) -> Project:
    if name is not None:
        project.name = name
    if inputs is not None:
        _apply_calc(project, inputs)
    db.commit()
    db.refresh(project)
    return project


def recalculate_project(db: Session, project: Project) -> Project:
    """Explicitly re-run a stored study on the current engine version."""
    _apply_calc(project, ProjectInputs.model_validate(project.inputs))
    db.commit()
    db.refresh(project)
    return project


def clone_project(db: Session, project: Project, name: str | None = None) -> Project:
    clone = Project(
        name=name or f"{project.name} (copy)",
        inputs=project.inputs,
        results=project.results,
        warnings=project.warnings,
        calculator_version=project.calculator_version,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone


def delete_project(db: Session, project: Project) -> None:
    db.delete(project)
    db.commit()
