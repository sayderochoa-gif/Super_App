"""
AI Reports and Anomaly Exploration Endpoints.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.reports import AIDailyReport, AIAnomaly
from app.models.earthquake import CuratedEarthquake
from app.schemas.reports import AIDailyReportOut, AIAnomalyOut
from app.security import get_current_user, get_current_user_flexible
from app.services.export_service import (
    export_earthquakes_to_csv,
    export_reports_to_csv,
    generate_pdf_report,
    generate_printable_html_report
)

router = APIRouter(prefix="/api/reports", tags=["AI Reports & Anomalies"])


@router.get("", response_model=List[AIDailyReportOut])
async def list_reports(
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns historical AI-generated daily executive reports."""
    stmt = select(AIDailyReport).order_by(desc(AIDailyReport.report_date)).limit(limit)
    res = await db.execute(stmt)
    reports = list(res.scalars().all())
    return reports


@router.get("/latest", response_model=Optional[AIDailyReportOut])
async def get_latest_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the most recent AI executive daily report."""
    stmt = select(AIDailyReport).order_by(desc(AIDailyReport.report_date)).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


@router.get("/anomalies", response_model=List[AIAnomalyOut])
async def list_anomalies(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns detected seismic anomalies and swarm clusters."""
    stmt = select(AIAnomaly).order_by(desc(AIAnomaly.detected_at)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/export")
async def export_data(
    export_type: str = Query("csv", pattern="^(csv|html|pdf)$"),
    target: str = Query("earthquakes", pattern="^(reports|earthquakes)$"),
    token: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_flexible),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports seismic activities and AI reports in CSV, PDF, or printable HTML format.
    Accepts JWT authentication via Authorization header or ?token= query parameter.
    """
    # 1. Fetch curated earthquake activities
    eq_stmt = select(CuratedEarthquake).order_by(desc(CuratedEarthquake.time)).limit(1000)
    eq_res = await db.execute(eq_stmt)
    events = list(eq_res.scalars().all())

    # 2. Fetch latest AI daily report
    rep_stmt = select(AIDailyReport).order_by(desc(AIDailyReport.report_date)).limit(1)
    rep_res = await db.execute(rep_stmt)
    latest_report = rep_res.scalar_one_or_none()

    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    # CSV Export
    if export_type == "csv":
        if target == "reports":
            rep_list_stmt = select(AIDailyReport).order_by(desc(AIDailyReport.report_date)).limit(30)
            rep_list_res = await db.execute(rep_list_stmt)
            csv_content = export_reports_to_csv(list(rep_list_res.scalars().all()))
            filename = f"sismowatch_reportes_{today_str}.csv"
        else:
            # Default target: earthquakes (Actividades sísmicas)
            csv_content = export_earthquakes_to_csv(events)
            filename = f"sismowatch_actividades_sismicas_{today_str}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # PDF Export (Native PDF Binary via ReportLab)
    elif export_type == "pdf":
        pdf_bytes = generate_pdf_report(latest_report, events)
        filename = f"sismowatch_informe_sismico_{today_str}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # HTML / Print Export
    else:
        html_content = generate_printable_html_report(latest_report, events)
        return Response(
            content=html_content,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": "inline"}
        )
