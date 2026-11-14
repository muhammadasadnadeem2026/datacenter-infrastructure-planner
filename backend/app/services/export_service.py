"""CSV and XLSX exports built from the authoritative engine result."""

from __future__ import annotations

import csv
import io
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from app.services.tabular import sheets

SHEET_SLUGS = {
    "inputs": "Inputs",
    "results": "Results",
    "devices": "Device Load List",
    "racks": "Rack Summary",
    "capacity": "Capacity Balance",
    "warnings": "Warnings",
    "calculations": "Calculations",
}


def _cell(v: Any) -> Any:
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


def to_csv(inputs: dict[str, Any], result: dict[str, Any], sheet_slug: str) -> str:
    name = SHEET_SLUGS.get(sheet_slug)
    if name is None:
        raise ValueError(f"unknown sheet '{sheet_slug}'")
    header, rows = sheets(inputs, result)[name]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows([[_cell(c) for c in row] for row in rows])
    return buf.getvalue()


def to_xlsx(inputs: dict[str, Any], result: dict[str, Any], project_name: str) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)
    head_font = Font(name="Inter", bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="09132B")
    for name, (header, rows) in sheets(inputs, result).items():
        ws = wb.create_sheet(name[:31])
        ws.append(header)
        for c in ws[1]:
            c.font = head_font
            c.fill = head_fill
        for row in rows:
            ws.append([_cell(c) for c in row])
        for i, _ in enumerate(header, start=1):
            ws.column_dimensions[get_column_letter(i)].width = 22 if i > 1 else 28
        ws.freeze_panes = "A2"
    meta = wb.create_sheet("About", 0)
    meta.append(["HallPlan — Data Center Infrastructure Planning Export"])
    meta["A1"].font = Font(name="Inter", bold=True, size=14, color="FFFFFF")
    meta["A1"].fill = head_fill
    meta.merge_cells("A1:B1")
    meta.append(["Project", project_name])
    meta.append(["Engine version", result["engine_version"]])
    meta.append(["Calculated at", result["calculated_at"]])
    meta.append(["Mode", result["mode"]])
    meta.column_dimensions["A"].width = 18
    meta.column_dimensions["B"].width = 40
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
