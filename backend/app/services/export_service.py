"""
Export Service for SismoWatch Reports and Events.
Generates CSV streams and formatted printable HTML representations.
"""

import io
import csv
from typing import List, Dict, Any
from app.models.reports import AIDailyReport
from app.models.earthquake import CuratedEarthquake


def export_earthquakes_to_csv(events: List[CuratedEarthquake]) -> str:
    """Exports earthquake records to standard CSV format."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "time", "magnitude", "place", "latitude", "longitude",
        "depth_km", "tsunami", "alert", "magType", "url"
    ])
    for ev in events:
        writer.writerow([
            ev.id,
            ev.time.isoformat() if ev.time else "",
            ev.mag,
            ev.place or "",
            ev.latitude,
            ev.longitude,
            ev.depth_km,
            ev.tsunami,
            ev.alert or "",
            ev.magType or "",
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


def generate_printable_html_report(report: AIDailyReport) -> str:
    """
    Renders an executive, print-ready HTML page with CSS print media queries.
    Suitable for browser Save-As-PDF or direct printing.
    """
    kpis = report.structured_kpis or {}
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>SismoWatch Informe Diario - {report.report_date}</title>
    <style>
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; margin: 40px; color: #1e293b; line-height: 1.6; }}
        .header {{ border-bottom: 2px solid #0284c7; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }}
        h1 {{ color: #0f172a; margin: 0; font-size: 24px; }}
        .badge {{ background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 9999px; font-size: 13px; font-weight: 600; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }}
        .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; text-align: center; }}
        .kpi-card .val {{ font-size: 22px; font-weight: 700; color: #0284c7; }}
        .kpi-card .lbl {{ font-size: 12px; color: #64748b; text-transform: uppercase; margin-top: 5px; }}
        .narrative {{ background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; white-space: pre-wrap; }}
        .footer {{ margin-top: 40px; font-size: 12px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
        @media print {{
            body {{ margin: 20px; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>SismoWatch — Informe Ejecutivo de Sismicidad</h1>
            <p style="margin: 4px 0 0; color: #64748b;">Fecha del Reporte: {report.report_date}</p>
        </div>
        <div>
            <span class="badge">Modelo: {report.model_name}</span>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="val">{kpis.get('total_events', 0)}</div>
            <div class="lbl">Total Eventos</div>
        </div>
        <div class="kpi-card">
            <div class="val">M {kpis.get('max_magnitude', 0.0)}</div>
            <div class="lbl">Magnitud Máxima</div>
        </div>
        <div class="kpi-card">
            <div class="val">M {kpis.get('avg_magnitude', 0.0)}</div>
            <div class="lbl">Magnitud Promedio</div>
        </div>
        <div class="kpi-card">
            <div class="val">{kpis.get('tsunami_alerts', 0)}</div>
            <div class="lbl">Alertas Tsunami</div>
        </div>
    </div>

    <div class="narrative">
{report.narrative_text}
    </div>

    <div class="footer">
        Generado por SismoWatch SuperApp Platform • Tokens: {report.tokens_used} • Latencia: {report.latency_sec}s
    </div>
</body>
</html>
"""
    return html
