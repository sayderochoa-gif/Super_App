"""
Statistical and Timeseries Endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database import get_db
from app.models.user import User
from app.schemas.pipeline import TimeseriesResponse
from app.security import get_current_user
from app.services.earthquake_service import get_hourly_timeseries
from app.models.earthquake import CuratedEarthquake

router = APIRouter(prefix="/api/stats", tags=["Statistics & Timeseries"])


@router.get("/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns time-bucketed counts and magnitude aggregates for charts.
    """
    points = await get_hourly_timeseries(db, hours=hours)
    return {"data": points}


@router.get("/magnitude-distribution")
async def get_magnitude_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns counts grouped into standard seismological magnitude tiers.
    """
    query = text("""
        SELECT
            CASE
                WHEN mag < 3.0 THEN 'Micro (< 3.0)'
                WHEN mag >= 3.0 AND mag < 4.5 THEN 'Minor (3.0 - 4.4)'
                WHEN mag >= 4.5 AND mag < 6.0 THEN 'Moderate (4.5 - 5.9)'
                ELSE 'Strong (>= 6.0)'
            END as tier,
            COUNT(*) as count
        FROM curated.earthquakes
        GROUP BY 1
        ORDER BY count DESC;
    """)
    res = await db.execute(query)
    rows = res.fetchall()

    return [{"tier": r[0], "count": int(r[1])} for r in rows]
