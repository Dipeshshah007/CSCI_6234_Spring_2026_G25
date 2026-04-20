"""
utils/exporter.py
-----------------
Feature 3: Export Reports to PDF and CSV
- PDF uses reportlab (pip install reportlab)
- CSV uses Python's built-in csv module
"""
import csv
import os
from datetime import date
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Color palette matching the app UI
COLOR_DARK   = colors.HexColor("#1A1F36")
COLOR_ACCENT = colors.HexColor("#4F6EF7")
COLOR_GREEN  = colors.HexColor("#10B981")
COLOR_RED    = colors.HexColor("#EF4444")
COLOR_LIGHT  = colors.HexColor("#F4F6FB")
COLOR_WHITE  = colors.white

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exports")


def _ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    return EXPORT_DIR


def _get_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle",
        fontSize=20, textColor=COLOR_WHITE, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=4)
    sub_style = ParagraphStyle("ReportSub",
        fontSize=10, textColor=colors.HexColor("#D0D9FF"),
        alignment=TA_CENTER, fontName="Helvetica", spaceAfter=2)
    section_style = ParagraphStyle("SectionHeader",
        fontSize=13, textColor=COLOR_DARK, fontName="Helvetica-Bold",
        spaceBefore=16, spaceAfter=6)
    return title_style, sub_style, section_style


def _header_block(elements, title_style, sub_style, report_name: str):
    """Draws a colored header band."""
    header_data = [[Paragraph(f"📚 Library Management System", title_style)],
                   [Paragraph(f"{report_name}  ·  Generated: {date.today().isoformat()}", sub_style)],
                   [Paragraph("CSCI 6234 — Object-Oriented Design  |  Prof. Walt Melo  |  Group G25", sub_style)]]
    header_table = Table(header_data, colWidths=["100%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COLOR_ACCENT),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 20),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 20),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.4 * cm))


def _styled_table(data, col_widths=None):
    """Builds a nicely styled table."""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0), COLOR_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), COLOR_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        # Data rows
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("ALIGN",         (0, 1), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [COLOR_WHITE, COLOR_LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, COLOR_ACCENT),
    ]))
    return t


# ── PDF Exports ───────────────────────────────────────────────────────────

def export_full_report_pdf(summary: dict, top_books: list,
                            overdue: list, all_loans: list) -> str:
    """Exports the full librarian report as a PDF. Returns file path."""
    _ensure_export_dir()
    filename = os.path.join(EXPORT_DIR, f"full_report_{date.today().isoformat()}.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    title_style, sub_style, section_style = _get_styles()

    _header_block(elements, title_style, sub_style, "Full Library Report")

    # ── Summary Section ──
    elements.append(Paragraph("Summary", section_style))
    sum_data = [["Metric", "Value"]] + [[k, str(v)] for k, v in summary.items()]
    elements.append(_styled_table(sum_data, col_widths=[10*cm, 6*cm]))
    elements.append(Spacer(1, 0.5*cm))

    # ── Top Borrowed Books ──
    elements.append(Paragraph("Top Borrowed Books", section_style))
    if top_books:
        tb_data = [["Title", "Author", "Times Borrowed"]] + [list(r) for r in top_books]
        elements.append(_styled_table(tb_data, col_widths=[8*cm, 6*cm, 4*cm]))
    else:
        elements.append(Paragraph("No data available.", getSampleStyleSheet()["Normal"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── Overdue Loans ──
    elements.append(Paragraph("Overdue Loans", section_style))
    if overdue:
        od_data = [["Member", "Book", "Due Date", "Days Overdue"]] + [list(r) for r in overdue]
        t = _styled_table(od_data, col_widths=[5*cm, 6*cm, 4*cm, 3*cm])
        # Color overdue rows red
        for i in range(1, len(od_data)):
            t.setStyle(TableStyle([("TEXTCOLOR", (3, i), (3, i), COLOR_RED)]))
        elements.append(t)
    else:
        elements.append(Paragraph("No overdue loans.", getSampleStyleSheet()["Normal"]))
    elements.append(Spacer(1, 0.5*cm))

    # ── All Loans ──
    elements.append(Paragraph("All Loan Records", section_style))
    if all_loans:
        al_data = [["Loan ID", "Member", "Book", "Loan Date", "Due Date", "Returned", "Status"]]
        al_data += [list(r) for r in all_loans]
        elements.append(_styled_table(al_data,
                         col_widths=[2*cm, 3.5*cm, 4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm]))
    doc.build(elements)
    return filename


def export_overdue_pdf(overdue: list) -> str:
    """Exports only the overdue report."""
    _ensure_export_dir()
    filename = os.path.join(EXPORT_DIR, f"overdue_report_{date.today().isoformat()}.pdf")
    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    elements = []
    title_style, sub_style, section_style = _get_styles()
    _header_block(elements, title_style, sub_style, "Overdue Loans Report")

    if overdue:
        data = [["Member", "Email", "Book", "Due Date", "Days Overdue", "Fine ($)"]]
        data += [list(r) for r in overdue]
        elements.append(_styled_table(data,
                         col_widths=[3.5*cm, 4*cm, 4*cm, 2.5*cm, 2.5*cm, 2*cm]))
    else:
        elements.append(Spacer(1, 1*cm))
        elements.append(Paragraph("✅ No overdue loans!", getSampleStyleSheet()["Normal"]))
    doc.build(elements)
    return filename


# ── CSV Exports ───────────────────────────────────────────────────────────

def export_loans_csv(all_loans: list) -> str:
    """Exports all loan records to CSV."""
    _ensure_export_dir()
    filename = os.path.join(EXPORT_DIR, f"loans_{date.today().isoformat()}.csv")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Loan ID", "Member", "Book Title",
                          "Loan Date", "Due Date", "Return Date", "Status"])
        writer.writerows(all_loans)
    return filename


def export_fines_csv(all_fines: list) -> str:
    """Exports all fine records to CSV."""
    _ensure_export_dir()
    filename = os.path.join(EXPORT_DIR, f"fines_{date.today().isoformat()}.csv")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Fine ID", "Member", "Book", "Amount ($)", "Status"])
        writer.writerows(all_fines)
    return filename


def export_summary_csv(summary: dict) -> str:
    """Exports the summary report to CSV."""
    _ensure_export_dir()
    filename = os.path.join(EXPORT_DIR, f"summary_{date.today().isoformat()}.csv")
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        for k, v in summary.items():
            writer.writerow([k, v])
    return filename
