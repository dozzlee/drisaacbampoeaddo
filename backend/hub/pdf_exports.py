from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle


NAVY = colors.HexColor("#122233")
MINT = colors.HexColor("#C8F0D9")
CANVAS = colors.HexColor("#F3F7F5")
MUTED = colors.HexColor("#667A89")
LINE = colors.HexColor("#DCE5E1")


def _text(value, style):
    return Paragraph(escape(str(value or "-")), style)


def build_tribute_register_pdf(parties, attachments_by_party):
    buffer = BytesIO()
    page_width, _ = landscape(A4)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=11 * mm,
        rightMargin=11 * mm,
        topMargin=15 * mm,
        bottomMargin=14 * mm,
        title="Tribute Register",
        author="Oko and Atteh Teams Hub",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("RegisterTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=23, textColor=NAVY, spaceAfter=3 * mm)
    meta_style = ParagraphStyle("RegisterMeta", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED)
    cell_style = ParagraphStyle("RegisterCell", parent=styles["BodyText"], fontName="Helvetica", fontSize=6.7, leading=8.4, textColor=NAVY)
    header_style = ParagraphStyle("RegisterHeader", parent=cell_style, fontName="Helvetica-Bold", fontSize=6.6, leading=8, textColor=colors.white, alignment=TA_CENTER)
    small_style = ParagraphStyle("RegisterSmall", parent=cell_style, fontSize=6.2, leading=7.5, textColor=MUTED)

    generated = timezone.localtime().strftime("%d %B %Y, %H:%M")
    story = [
        Paragraph("Tribute Register", title_style),
        Paragraph(f"Complete list of {len(parties)} interested parties - generated {escape(generated)}", meta_style),
        Spacer(1, 5 * mm),
    ]
    headers = ["Person or organisation", "Contact", "Responsible person", "Request", "Tribute", "Supporting files", "Tribute files"]
    data = [[Paragraph(label, header_style) for label in headers]]
    for party in parties:
        attachments = attachments_by_party.get(party.id, [])
        supporting = [item.original_name for item in attachments if item.attachment_type != "tribute"]
        tributes = [item.original_name for item in attachments if item.attachment_type == "tribute"]
        data.append([
            _text(party.name, cell_style),
            _text(party.phone or "Not provided", small_style),
            _text(party.assigned_to or "Unassigned", cell_style),
            _text(party.request_status, cell_style),
            _text(party.tribute_status, cell_style),
            _text(", ".join(supporting) if supporting else "None", small_style),
            _text(", ".join(tributes) if tributes else "None", small_style),
        ])

    usable_width = page_width - doc.leftMargin - doc.rightMargin
    column_weights = [1.55, 0.82, 1.05, 0.72, 0.72, 1.25, 1.25]
    weight_total = sum(column_weights)
    column_widths = [usable_width * weight / weight_total for weight in column_weights]
    table = LongTable(data, colWidths=column_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CANVAS]),
    ]))
    story.append(table)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(MINT)
        canvas.setLineWidth(1.2)
        canvas.line(document.leftMargin, 9 * mm, page_width - document.rightMargin, 9 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(document.leftMargin, 5.5 * mm, "Oko and Atteh Teams Hub")
        canvas.drawRightString(page_width - document.rightMargin, 5.5 * mm, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    buffer.seek(0)
    return buffer
