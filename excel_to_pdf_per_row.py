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

def reshape_arabic(text):
    """Reshape Arabic letters, then apply BiDi with RTL base direction."""
    if not isinstance(text, str):
        return str(text)
    # 1. Connect Arabic letters
    reshaped = arabic_reshaper.reshape(text)
    # 2. Reorder for visual display (RTL base)
    return get_display(reshaped, base_dir='R')

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

    # Right‑aligned for both table and paragraph to keep RTL text wrapping correctly
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=base_style,
        fontSize=10,
        alignment=2,  # RIGHT
    )

    table_data = []
    for col in COLUMNS:
        if col in agent_data:
            field_display = reshape_arabic(col)
            value_raw = agent_data[col]
            if pd.isna(value_raw):
                value_str = ''
            else:
                value_str = str(value_raw)

            # Preserve line breaks for "ملاحظات"
            if col == 'ملاحظات' and value_str:
                lines = value_str.splitlines()
                reshaped_lines = [reshape_arabic(line) for line in lines]
                value_display = '<br/>'.join(reshaped_lines)
            else:
                value_display = reshape_arabic(value_str)

            table_data.append([
                Paragraph(field_display, cell_style),
                Paragraph(value_display, cell_style)
            ])

    col_widths = [doc.width * 0.25, doc.width * 0.75]
    table = Table(table_data, colWidths=col_widths, repeatRows=0)

    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,-1), 'RIGHT'),   # field names right‑aligned
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),   # values right‑aligned (fixes wrapping)
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('BACKGROUND', (1,0), (1,-1), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))

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

if __name__ == "__main__":
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = input("Enter path to Excel file: ").strip()
        if not excel_file:
            print("No file provided. Exiting.")
            sys.exit(1)

    if len(sys.argv) > 2:
        out_dir = sys.argv[2]
    else:
        out_dir = OUTPUT_DIR

    generate_reports(excel_file, out_dir)
    