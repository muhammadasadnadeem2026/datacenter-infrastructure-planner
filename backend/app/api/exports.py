"""Report and export endpoints. Inputs are re-validated and recalculated server-side."""

from __future__ import annotations

import re

from fastapi import APIRouter, Response

from app.calculations.full import run_full_calculation
from app.schemas.inputs import ReportRequest
from app.services.export_service import SHEET_SLUGS, to_csv, to_xlsx
from app.services.report_service import build_pdf

router = APIRouter(prefix="/api/export", tags=["export"])


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_")[:60] or "project"


def _calc(body: ReportRequest) -> tuple[dict, dict]:
    inputs = body.inputs.model_dump(mode="json")
    return inputs, run_full_calculation(body.inputs).to_dict()


@router.post("/pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
def export_pdf(body: ReportRequest):
    inputs, result = _calc(body)
    pdf = build_pdf(body.project_name, inputs, result)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{_slug(body.project_name)}_report.pdf"'})


@router.post("/xlsx", response_class=Response)
def export_xlsx(body: ReportRequest):
    inputs, result = _calc(body)
    data = to_xlsx(inputs, result, body.project_name)
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{_slug(body.project_name)}.xlsx"'})


@router.post("/csv/{sheet}", response_class=Response, description=f"sheet: {', '.join(SHEET_SLUGS)}")
def export_csv(sheet: str, body: ReportRequest):
    inputs, result = _calc(body)
    text = to_csv(inputs, result, sheet)
    return Response(text, media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{_slug(body.project_name)}_{sheet}.csv"'})
