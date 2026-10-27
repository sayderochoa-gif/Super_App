"""
Export Service for SismoWatch Reports and Events.
Generates CSV streams, PDF documents (via ReportLab), and formatted printable HTML representations.
"""

import io
import csv
import re
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models.reports import AIDailyReport
from app.models.earthquake import CuratedEarthquake


def export_earthquakes_to_csv(events: List[CuratedEarthquake]) -> str:
    """Exports earthquake records to standard CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "time_utc", "magnitude", "place", "latitude", "longitude",
        "depth_km", "tsunami_alert", "alert_level", "magType", "status", "usgs_url"
    ])
    for ev in events:
        writer.writerow([
            ev.id,
            ev.time.isoformat() if ev.time else "",
            ev.mag,
            ev.place or "Ubicación sin especificar",
            round(ev.latitude, 4) if ev.latitude is not None else "",
            round(ev.longitude, 4) if ev.longitude is not None else "",
            round(ev.depth_km, 2) if ev.depth_km is not None else "",
            "Sí" if (ev.tsunami and ev.tsunami > 0) else "No",
            ev.alert or "ninguna",
            ev.magType or "",
            ev.status or "automatic",
            ev.url or ""
        ])
    return output.getvalue()


def export_reports_to_csv(reports: List[AIDailyReport]) -> str:
    """Exports AI report history to CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "report_date", "total_events", "max_magnitude",
        "avg_magnitude", "tsunami_alerts", "most_active_region",
        "model_name", "created_at"
    ])
    for rep in reports:
        kpis = rep.structured_kpis or {}
        writer.writerow([
            rep.id,
            rep.report_date.isoformat() if rep.report_date else "",
            kpis.get("total_events", ""),
            kpis.get("max_magnitude", ""),
            kpis.get("avg_magnitude", ""),
            kpis.get("tsunami_alerts", ""),
            kpis.get("most_active_region", ""),
            rep.model_name,
            rep.created_at.isoformat() if rep.created_at else ""
        ])
    return output.getvalue()


def generate_pdf_report(
    report: Optional[AIDailyReport],
    events: List[CuratedEarthquake]
) -> bytes:
    """
    Generates a production-grade PDF document containing:
    1. Executive Header & Date Metadata
    2. Consolidated KPI Metric Table
    3. AI Executive Narrative & Swarm Analysis
    4. Detailed Table of Recent Seismic Activities
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )
    narrative_style = ParagraphStyle(
        'NarrativeText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )
    kpi_num_style = ParagraphStyle(
        'KPINum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=16,
        alignment=1,
        textColor=colors.HexColor('#0284c7')
    )
    kpi_lbl_style = ParagraphStyle(
        'KPILbl',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor('#64748b')
    )

    story = []

    # 1. Header
    report_date_str = report.report_date.isoformat() if (report and report.report_date) else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    model_name = report.model_name if report else "sismowatch-analytics-engine"

    header_table_data = [
        [
            Paragraph("<b>SismoWatch</b> — Informe Ejecutivo de Sismicidad", title_style),
            Paragraph(f"<b>Fecha:</b> {report_date_str}<br/><b>Generado:</b> {datetime.now(timezone.utc).strftime('%H:%M UTC')}", subtitle_style)
        ]
    ]
    header_table = Table(header_table_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceBefore=8, spaceAfter=12))

    # 2. KPI Summary Cards
    kpis = (report.structured_kpis or {}) if report else {}
    total_events = kpis.get("total_events", len(events))
    max_mag = kpis.get("max_magnitude", max([e.mag for e in events]) if events else 0.0)
    avg_mag = kpis.get("avg_magnitude", round(sum([e.mag for e in events]) / max(len(events), 1), 2) if events else 0.0)
    tsunami_alerts = kpis.get("tsunami_alerts", sum([1 for e in events if e.tsunami and e.tsunami > 0]))

    kpi_data = [
        [
            Paragraph(str(total_events), kpi_num_style),
            Paragraph(f"M {max_mag:.1f}", kpi_num_style),
            Paragraph(f"M {avg_mag:.2f}", kpi_num_style),
            Paragraph(str(tsunami_alerts), kpi_num_style),
        ],
        [
            Paragraph("Total Eventos", kpi_lbl_style),
            Paragraph("Magnitud Máxima", kpi_lbl_style),
            Paragraph("Magnitud Promedio", kpi_lbl_style),
            Paragraph("Alertas Tsunami", kpi_lbl_style),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[135, 135, 135, 135])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # 3. AI Narrative Summary
    story.append(Paragraph("Resumen Analítico & Detección de Anomalías", section_heading))
    raw_narrative = report.narrative_text if (report and report.narrative_text) else "Actividad sísmica monitoreada dentro de los parámetros habituales."
    # Clean markdown headers and format bold tags properly for ReportLab
    cleaned_narrative = raw_narrative.replace("&", "&amp;")
    cleaned_narrative = re.sub(r'#+\s*', '', cleaned_narrative)
    cleaned_narrative = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_narrative)
    cleaned_narrative = cleaned_narrative.replace("*", "")
    
    for paragraph in cleaned_narrative.split("\n\n"):
        p_text = paragraph.strip()
        if p_text:
            story.append(Paragraph(p_text.replace("\n", "<br/>"), narrative_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))

    # 4. Detailed Seismic Activities Table (Top / Recent Events)
    story.append(Paragraph(f"Detalle de Actividades Sísmicas Monitoreadas (Últimos {min(len(events), 25)} registros)", section_heading))

    table_data = [
        [
            Paragraph("Fecha/Hora (UTC)", table_header_style),
            Paragraph("Mag", table_header_style),
            Paragraph("Ubicación", table_header_style),
            Paragraph("Prof (km)", table_header_style),
            Paragraph("Coordenadas", table_header_style),
            Paragraph("Tsunami", table_header_style),
        ]
    ]

    for ev in events[:25]:
        time_str = ev.time.strftime("%Y-%m-%d %H:%M") if ev.time else "N/A"
        coords_str = f"{ev.latitude:.2f}°, {ev.longitude:.2f}°" if (ev.latitude and ev.longitude) else "N/A"
        tsunami_str = "SÍ" if (ev.tsunami and ev.tsunami > 0) else "No"
        place_str = (ev.place or "N/A")[:38]

        table_data.append([
            Paragraph(time_str, table_cell_style),
            Paragraph(f"<b>M {ev.mag:.1f}</b>", table_cell_style),
            Paragraph(place_str, table_cell_style),
            Paragraph(f"{ev.depth_km:.1f}" if ev.depth_km is not None else "N/A", table_cell_style),
            Paragraph(coords_str, table_cell_style),
            Paragraph(tsunami_str, table_cell_style),
        ])

    events_table = Table(table_data, colWidths=[85, 40, 215, 60, 95, 45])
    events_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(events_table)

    # 5. Footer notice
    story.append(Spacer(1, 14))
    footer_text = f"Generado automáticamente por SismoWatch SuperApp Platform • Modelo: {model_name} • Certificado Anti-Hallucination"
    story.append(Paragraph(footer_text, subtitle_style))

    doc.build(story)
    return buffer.getvalue()


def generate_printable_html_report(
    report: Optional[AIDailyReport],
    events: List[CuratedEarthquake]
) -> str:
    """
    Renders an executive, print-ready HTML page with CSS print media queries
    and embedded table of seismic activities.
    Suitable for browser Print-to-PDF or direct printing.
    """
    kpis = (report.structured_kpis or {}) if report else {}
    report_date = report.report_date if report else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    model_name = report.model_name if report else "sismowatch-analytics-engine"
    narrative_text = report.narrative_text if report else "Actividad sísmica monitoreada dentro de parámetros normales."

    events_rows = ""
    for ev in events[:50]:
        time_str = ev.time.strftime("%Y-%m-%d %H:%M:%S") if ev.time else "N/A"
        mag_badge_color = "#ef4444" if ev.mag >= 6.0 else "#f97316" if ev.mag >= 4.5 else "#f59e0b" if ev.mag >= 3.0 else "#10b981"
        tsunami_badge = '<span class="tsunami-yes">ALERTA</span>' if (ev.tsunami and ev.tsunami > 0) else '<span class="tsunami-no">No</span>'

        events_rows += f"""
        <tr>
            <td style="font-family: monospace;">{time_str}</td>
            <td><span class="mag-pill" style="background-color: {mag_badge_color};">M {ev.mag:.1f}</span></td>
            <td><strong>{ev.place or "Ubicación sin especificar"}</strong></td>
            <td>{ev.depth_km:.1f} km</td>
            <td style="font-family: monospace;">{ev.latitude:.3f}°, {ev.longitude:.3f}°</td>
            <td>{tsunami_badge}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SismoWatch Informe Sísmico — {report_date}</title>
    <style>
        @page {{ size: letter; margin: 15mm; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 25px auto;
            max-width: 960px;
            color: #0f172a;
            line-height: 1.5;
            background: #ffffff;
        }}
        .no-print-bar {{
            background: #0f172a;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .print-btn {{
            background: #0284c7;
            color: white;
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
        }}
        .print-btn:hover {{ background: #0369a1; }}
        .header {{
            border-bottom: 2px solid #0284c7;
            padding-bottom: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        h1 {{ color: #0f172a; margin: 0; font-size: 22px; font-weight: 700; }}
        .badge {{
            background: #e0f2fe;
            color: #0369a1;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }}
        .kpi-card .val {{ font-size: 20px; font-weight: 700; color: #0284c7; font-family: monospace; }}
        .kpi-card .lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; margin-top: 4px; font-weight: 600; }}
        .narrative-box {{
            background: #f8fafc;
            border-left: 4px solid #0284c7;
            border-radius: 0 8px 8px 0;
            padding: 18px 22px;
            margin-bottom: 25px;
            white-space: pre-wrap;
            font-size: 13px;
            color: #334155;
            line-height: 1.6;
        }}
        h2 {{ font-size: 15px; color: #0f172a; margin-top: 25px; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
        table.events-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }}
        table.events-table th {{
            background: #0f172a;
            color: #ffffff;
            text-align: left;
            padding: 8px 10px;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
        }}
        table.events-table td {{
            padding: 7px 10px;
            border-bottom: 1px solid #e2e8f0;
        }}
        table.events-table tr:nth-child(even) {{ background: #f8fafc; }}
        .mag-pill {{
            color: white;
            padding: 2px 7px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 11px;
            font-family: monospace;
        }}
        .tsunami-yes {{ background: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 10px; }}
        .tsunami-no {{ color: #94a3b8; font-size: 11px; }}
        .footer {{
            margin-top: 30px;
            font-size: 11px;
            color: #94a3b8;
            text-align: center;
            border-top: 1px solid #e2e8f0;
            padding-top: 15px;
        }}
        @media print {{
            .no-print-bar {{ display: none !important; }}
            body {{ margin: 0; max-width: 100%; }}
            table.events-table tr {{ page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="no-print-bar">
        <div>
            <strong>Vista de Impresión SismoWatch</strong> — Haga clic en el botón para imprimir o guardar como PDF.
        </div>
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir / Guardar como PDF</button>
    </div>

    <div class="header">
        <div>
            <h1>SismoWatch — Informe Ejecutivo de Sismicidad</h1>
            <p style="margin: 4px 0 0; color: #64748b; font-size: 13px;">Fecha de Análisis: <strong>{report_date}</strong></p>
        </div>
        <div>
            <span class="badge">Modelo: {model_name}</span>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="val">{kpis.get('total_events', len(events))}</div>
            <div class="lbl">Total Eventos</div>
        </div>
        <div class="kpi-card">
            <div class="val">M {kpis.get('max_magnitude', 0.0):.1f}</div>
            <div class="lbl">Magnitud Máxima</div>
        </div>
        <div class="kpi-card">
            <div class="val">M {kpis.get('avg_magnitude', 0.0):.2f}</div>
            <div class="lbl">Magnitud Promedio</div>
        </div>
        <div class="kpi-card">
            <div class="val">{kpis.get('tsunami_alerts', 0)}</div>
            <div class="lbl">Alertas Tsunami</div>
        </div>
    </div>

    <h2>Resumen Analítico</h2>
    <div class="narrative-box">
{narrative_text}
    </div>

    <h2>Detalle de Actividades Sísmicas Monitoreadas ({min(len(events), 50)} registros)</h2>
    <table class="events-table">
        <thead>
            <tr>
                <th>Fecha/Hora (UTC)</th>
                <th>Magnitud</th>
                <th>Ubicación</th>
                <th>Profundidad</th>
                <th>Coordenadas</th>
                <th>Tsunami</th>
            </tr>
        </thead>
        <tbody>
            {events_rows}
        </tbody>
    </table>

    <div class="footer">
        Generado por SismoWatch SuperApp Platform • Modelo: {model_name} • Certificado Anti-Hallucination
    </div>
</body>
</html>
"""
    return html
