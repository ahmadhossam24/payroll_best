#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

from PySide6.QtWidgets import QFileDialog, QWidget, QMessageBox

# ---------- Configuration ----------
FONT_PATH = 'C:/Windows/Fonts/ARIALUNI.TTF'   # or your Arabic font
COLUMNS = [
    'اسم الايجنت',
    'الاساسي',
    'الاساسي بعد الخصم',
    'الكوالتي',
    'الكوالتي بعد خصم النقاط',
    'التارجت',
    'اكتيف',
    'الكوميشن',
    'المرتب',
    'ملاحظات'
]
OUTPUT_DIR = 'reports'
# ---------- End Configuration ----------

# Columns that should have a grey background (only their value cells)
GREY_COLUMNS = {
    'الاساسي بعد الخصم',
    'الكوالتي بعد خصم النقاط',
    'الكوميشن',
    'المرتب'
}

def reshape_arabic(text):
    """Reshape Arabic letters, then apply BiDi with RTL base direction."""
    if not isinstance(text, str):
        return str(text)
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped, base_dir='R')

def format_value(value):
    """
    Convert numeric values to integer strings (drop .0) if they are whole numbers.
    If not numeric, return the original string representation.
    """
    if pd.isna(value):
        return ''
    try:
        # Try to convert to float
        num = float(value)
        # If it's a whole number, show as integer
        if num.is_integer():
            return str(int(num))
        else:
            # Keep as float with one decimal? or keep original string? We'll keep original string.
            return str(value)
    except (ValueError, TypeError):
        # Not a number, return as string
        return str(value)

def create_agent_pdf(agent_data, agent_name, output_path, font_name):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )

    styles = getSampleStyleSheet()
    base_style = styles['Normal']
    base_style.fontName = font_name
    base_style.fontSize = 10

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=16,
        alignment=1,  # center
        spaceAfter=0.5*cm,
    )

    cell_style = ParagraphStyle(
        'CellStyle',
        parent=base_style,
        fontSize=10,
        alignment=2,  # RIGHT
    )

    table_data = []
    grey_row_indices = []

    for row_idx, col in enumerate(COLUMNS):
        if col not in agent_data:
            continue
        field_display = reshape_arabic(col)
        value_raw = agent_data[col]

        # Special handling for 'ملاحظات' – keep raw text (with line breaks)
        if col == 'ملاحظات':
            if pd.isna(value_raw):
                value_str = ''
            else:
                value_str = str(value_raw)
            # Preserve line breaks
            lines = value_str.splitlines()
            reshaped_lines = [reshape_arabic(line) for line in lines]
            value_display = '<br/>'.join(reshaped_lines)
        else:
            # Apply integer formatting to all other columns
            value_str = format_value(value_raw)
            value_display = reshape_arabic(value_str)

        table_data.append([
            Paragraph(field_display, cell_style),
            Paragraph(value_display, cell_style)
        ])

        # If this column needs grey background, record its row index
        if col in GREY_COLUMNS:
            grey_row_indices.append(row_idx)

    col_widths = [doc.width * 0.25, doc.width * 0.75]
    table = Table(table_data, colWidths=col_widths, repeatRows=0)

    # Build base style
    style_commands = [
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),   # field names right‑aligned
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),   # values right‑aligned
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),   # field names light grey
        ('BACKGROUND', (1,0), (1,-1), colors.white),       # values white by default
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]

    # Add grey background for the value cells of specified rows – using light grey to match field names
    for row_idx in grey_row_indices:
        style_commands.append(('BACKGROUND', (1, row_idx), (1, row_idx), colors.lightgrey))

    table.setStyle(TableStyle(style_commands))

    story = []
    if agent_name and agent_name.strip():
        title_text = reshape_arabic(f"تقرير {agent_name}")
    else:
        title_text = reshape_arabic("تقرير العميل")
    title_para = Paragraph(title_text, title_style)
    story.append(title_para)
    story.append(Spacer(1, 0.5*cm))
    story.append(table)

    doc.build(story)
    print(f"Created: {output_path}")

def generate_reports(excel_path, output_dir=OUTPUT_DIR):
    try:
        df = pd.read_excel(excel_path, engine='openpyxl')
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)

    available_cols = list(df.columns)
    missing = [col for col in COLUMNS if col not in available_cols]
    if missing:
        print(f"Warning: Missing columns: {missing}. Proceeding with available ones.")

    font_name = 'Helvetica'
    try:
        pdfmetrics.registerFont(TTFont('ArabicFont', FONT_PATH))
        font_name = 'ArabicFont'
        print(f"Font '{FONT_PATH}' registered successfully.")
    except Exception as e:
        print(f"Warning: Could not load font '{FONT_PATH}'. Using default Helvetica (Arabic may not display correctly).")
        print(f"Error: {e}")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for idx, row in df.iterrows():
        agent_data = {}
        for col in COLUMNS:
            if col in available_cols:
                agent_data[col] = row[col]
            else:
                agent_data[col] = None

        agent_name = agent_data.get('اسم الايجنت', '')
        if pd.isna(agent_name) or not str(agent_name).strip():
            agent_name = f"Agent_{idx+1}"
        else:
            agent_name = str(agent_name).strip()

        safe_name = "".join(c for c in agent_name if c.isalnum() or c in (' ', '_')).strip()
        if not safe_name:
            safe_name = f"Agent_{idx+1}"
        safe_name = safe_name.replace(' ', '_')
        pdf_filename = f"{safe_name}.pdf"
        output_path = os.path.join(output_dir, pdf_filename)

        create_agent_pdf(agent_data, agent_name, output_path, font_name)

    print(f"\nAll reports generated in '{output_dir}'")

def generate_reports_from_gui(parent: QWidget | None = None, excel_path: str | None = None, output_dir: str = OUTPUT_DIR):
    """
    Wrapper to call generate_reports. If excel_path is None, show a QFileDialog to pick the file.
    parent: optional QWidget to parent the file dialog (use self from your MainWindow).
    """
    # If caller provided a path, use it directly
    if excel_path:
        generate_reports(excel_path, output_dir)
        return

    # Otherwise ask the user to choose a file
    file_path, _ = QFileDialog.getOpenFileName(
        parent,
        "Select Excel file for reports",
        "",
        "Excel Files (*.xlsx *.xls)"
    )
    if not file_path:
        # user cancelled; optionally show a message or just return
        # QMessageBox.information(parent, "Cancelled", "No file selected.")  # optional
        return

    generate_reports(file_path, output_dir)
    QMessageBox.information(parent, "Convertion Complete", "pdfs generated in reports folder")  # optional