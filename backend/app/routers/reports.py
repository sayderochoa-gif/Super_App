"""
AI Reports and Anomaly Exploration Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.reports import AIDailyReport, AIAnomaly
from app.models.earthquake import CuratedEarthquake
from app.schemas.reports import AIDailyReportOut, AIAnomalyOut
from app.security import get_current_user
from app.services.export_service import (
    export_earthquakes_to_csv,
    export_reports_to_csv,
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
    target: str = Query("reports", pattern="^(reports|earthquakes)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exports reports or earthquakes in CSV or printable HTML format.
    """
    if target == "earthquakes":
        stmt = select(CuratedEarthquake).order_by(desc(CuratedEarthquake.time)).limit(1000)
        res = await db.execute(stmt)
        events = list(res.scalars().all())
        csv_content = export_earthquakes_to_csv(events)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sismowatch_earthquakes.csv"}
        )

    # Target: reports
    stmt = select(AIDailyReport).order_by(desc(AIDailyReport.report_date)).limit(30)
    res = await db.execute(stmt)
    reports = list(res.scalars().all())

    if export_type == "csv":
        csv_content = export_reports_to_csv(reports)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sismowatch_reports.csv"}
        )
    else:
        # Printable HTML (for PDF/browser printing)
        if not reports:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reports available to export.")
        latest_report = reports[0]
        html_content = generate_printable_html_report(latest_report)
        return Response(
            content=html_content,
            media_type="text/html",
            headers={"Content-Disposition": f"inline; filename=sismowatch_report_{latest_report.report_date}.html"}
        )
