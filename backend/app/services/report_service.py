"""PDF engineering report generated from the authoritative engine result."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.constants.disclaimer import DISCLAIMER
from app.services.tabular import MODULE_TITLES, display, flatten
from app.version import APP_NAME

REPORT_SECTIONS = [
    ("IT Load", ["it", "rack_count", "space"]),
    ("Electrical", ["circuit", "utility"]),
    ("Cooling", ["cooling", "environment"]),
    ("UPS", ["ups", "battery"]),
    ("PDU", ["pdu"]),
    ("Transformer", ["transformer"]),
    ("Generator", ["generator"]),
    ("BESS", ["bess"]),
    ("Energy", ["facility", "energy"]),
]

_REFS = Path(__file__).resolve().parents[1] / "constants" / "references.json"
ACCENT = colors.HexColor("#09132B")
BRAND_BLUE = colors.HexColor("#D98E1F")
TABLE_HEAD = colors.HexColor("#1E2761")
ZEBRA = colors.HexColor("#EEF3FC")


def _styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], textColor=ACCENT, fontSize=20),
        "h1": ParagraphStyle("h1", parent=ss["Heading1"], textColor=ACCENT, fontSize=14, spaceBefore=10),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontSize=11, spaceBefore=6, textColor=BRAND_BLUE),
        "body": ParagraphStyle("b", parent=ss["BodyText"], fontSize=8.5, leading=11),
        "cell": ParagraphStyle("c", parent=ss["BodyText"], fontSize=7, leading=8.5),
        "small": ParagraphStyle("s", parent=ss["BodyText"], fontSize=7.5, leading=9.5, textColor=colors.grey),
    }


def _table(header: list[str], rows: list[list[Any]], widths: list[float], st: dict) -> Table:
    data = [[Paragraph(f"<font color='white'><b>{h}</b></font>", st["cell"]) for h in header]]
    data += [[Paragraph(_esc(display(c) if not isinstance(c, str) else c), st["cell"]) for c in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEAD),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D3DF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
    ]))
    return t


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_pdf(project_name: str, inputs: dict[str, Any], result: dict[str, Any]) -> bytes:
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                            title=f"{project_name} - {APP_NAME} report")
    modules = result["modules"]
    story: list[Any] = []

    story += [Paragraph(f"{APP_NAME} — Data Center Infrastructure Planning Report", st["title"]),
              Paragraph(f"<b>Project:</b> {_esc(project_name)}", st["body"]),
              Paragraph(f"<b>Generated:</b> {result['calculated_at']}", st["body"]),
              Paragraph(f"<b>Calculation engine version:</b> {result['engine_version']} &nbsp; "
                        f"<b>Mode:</b> {result['mode']}", st["body"]),
              Spacer(1, 6), Paragraph(_esc(DISCLAIMER), st["small"]), Spacer(1, 8)]

    story.append(Paragraph("Summary", st["h1"]))
    summary_rows = []
    for card in result["summary"]:
        ref = card[result["unit_system"]]
        step = next(s for s in modules[ref["module"]]["steps"] if s["key"] == ref["key"])
        summary_rows.append([card["label"], step["value"], step["unit"]])
    story.append(_table(["Metric", "Value", "Unit"], summary_rows, [2.6 * inch, 1.6 * inch, 1.4 * inch], st))

    story.append(Paragraph("Design Inputs", st["h1"]))
    story.append(_table(["Field", "Value"], [[k, v] for k, v in flatten(inputs)], [3.6 * inch, 3.6 * inch], st))

    story.append(PageBreak())
    for title, keys in REPORT_SECTIONS:
        present = [k for k in keys if k in modules]
        if not present:
            continue
        story.append(Paragraph(title, st["h1"]))
        for k in present:
            story.append(Paragraph(MODULE_TITLES.get(k, k), st["h2"]))
            rows = [[s["label"], s["value"], s["unit"], s["formula"], s["substitution"]] for s in modules[k]["steps"]]
            story.append(_table(["Result", "Value", "Unit", "Formula", "Calculation"], rows,
                                [1.7 * inch, 0.8 * inch, 0.7 * inch, 2.0 * inch, 2.1 * inch], st))

    story.append(Paragraph("Capacity Balance", st["h1"]))
    cap = result["capacity"]
    story.append(_table(
        ["System", "Required", "Usable", "Unit", "Loading %", "Reserve", "Redundancy", "Status"],
        [[r["label"], r["required"], r["usable"], r["unit"], r["loading_pct"], r["reserve"], r["redundancy"],
          r["status"]] for r in cap["rows"]],
        [1.3 * inch, 0.85 * inch, 0.85 * inch, 0.75 * inch, 0.75 * inch, 0.85 * inch, 0.8 * inch, 0.9 * inch], st))
    if cap.get("bottleneck"):
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Bottleneck:</b> {_esc(cap['bottleneck']['message'])}", st["body"]))

    story.append(Paragraph("Warnings", st["h1"]))
    story.append(_table(["Severity", "Title", "Message", "System"],
                        [[w["severity"], w["title"], w["message"], w["affected_system"]] for w in result["warnings"]]
                        or [["—", "No warnings", "", ""]],
                        [0.8 * inch, 1.6 * inch, 3.9 * inch, 1.0 * inch], st))

    story.append(Paragraph("Assumptions", st["h1"]))
    assumptions = sorted({s["assumption"] for m in modules.values() for s in m["steps"] if s["assumption"]})
    for a in assumptions:
        story.append(Paragraph(f"• {_esc(a)}", st["body"]))

    story.append(Paragraph("References", st["h1"]))
    used = {s["reference"] for m in modules.values() for s in m["steps"] if s["reference"]}
    used |= {w["reference"] for w in result["warnings"] if w["reference"]}
    refs = [r for r in json.loads(_REFS.read_text(encoding="utf-8")) if r["id"] in used]
    for r in refs:
        story.append(Paragraph(
            f"<b>[{r['id']}]</b> {_esc(r['organization'])} — {_esc(r['document'])}; {_esc(r['section'])}. "
            f"<i>Status: {r['verification_status']}</i>", st["body"]))

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.grey)
        canvas.drawString(0.6 * inch, 0.4 * inch,
                          f"{APP_NAME} · engine {result['engine_version']} · {result['calculated_at'][:19]}Z")
        canvas.drawRightString(LETTER[0] - 0.6 * inch, 0.4 * inch, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
