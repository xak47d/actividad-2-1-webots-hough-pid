"""Genera un PDF base para la entrega de la Actividad 2.1.

El PDF se construye a partir del reporte en Markdown y del script Python
entregado. Se deja listo como plantilla editable para completar evidencia real
de Webots, ganancias finales del PID y el enlace del video en YouTube.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer


BASE_DIR = Path(__file__).resolve().parent
REPORT_MD = BASE_DIR / "Actividad_2_1_Entrega.md"
SCRIPT_PY = BASE_DIR / "symple_controller_act_2_1.py"
OUTPUT_PDF = BASE_DIR / "Actividad_2_1_Deteccion_de_Carriles_EquipoXX.pdf"


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CustomTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#17324d"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CustomHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#17324d"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CustomBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            fontName="Courier",
            fontSize=7,
            leading=8.5,
            leftIndent=6,
            rightIndent=6,
            spaceBefore=4,
            spaceAfter=4,
            backColor=colors.HexColor("#f2f4f7"),
        )
    )
    return styles


def markdown_to_story(markdown_text: str, styles) -> list:
    story = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            story.append(Spacer(1, 0.10 * inch))
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["CustomTitle"]))
            continue
        if line.startswith("## "):
            story.append(Paragraph(line[3:], styles["CustomHeading"]))
            continue
        if line.startswith("- "):
            bullet = "• " + line[2:]
            story.append(Paragraph(bullet, styles["CustomBody"]))
            continue
        if line.startswith("|"):
            story.append(Paragraph(line.replace("|", " | "), styles["CustomBody"]))
            continue
        story.append(Paragraph(line, styles["CustomBody"]))
    return story


def build_pdf() -> None:
    styles = build_styles()
    report_text = REPORT_MD.read_text(encoding="utf-8")
    script_text = SCRIPT_PY.read_text(encoding="utf-8")

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    story = markdown_to_story(report_text, styles)
    story.append(PageBreak())
    story.append(Paragraph("Anexo A. Script Python entregado", styles["CustomHeading"]))
    story.append(
        Paragraph(
            "El siguiente codigo corresponde al controlador principal desarrollado "
            "para la actividad.",
            styles["CustomBody"],
        )
    )
    story.append(Preformatted(script_text, styles["CodeBlock"]))

    doc.build(story)


if __name__ == "__main__":
    build_pdf()
