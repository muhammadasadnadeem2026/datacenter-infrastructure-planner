from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectOut, ProjectSummary, ProjectUpdate
from app.services import project_service as svc

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_or_404(db: Session, project_id: str) -> Project:
    project = svc.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Session = Depends(get_db)):
    return svc.list_projects(db)


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    return svc.create_project(db, body.name, body.inputs)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    return _get_or_404(db, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, body: ProjectUpdate, db: Session = Depends(get_db)):
    return svc.update_project(db, _get_or_404(db, project_id), body.name, body.inputs)


@router.post("/{project_id}/clone", response_model=ProjectOut, status_code=201)
def clone_project(project_id: str, db: Session = Depends(get_db)):
    return svc.clone_project(db, _get_or_404(db, project_id))


@router.post("/{project_id}/recalculate", response_model=ProjectOut,
             summary="Re-run a stored study on the current engine version")
def recalculate_project(project_id: str, db: Session = Depends(get_db)):
    return svc.recalculate_project(db, _get_or_404(db, project_id))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    svc.delete_project(db, _get_or_404(db, project_id))
    return Response(status_code=204)
