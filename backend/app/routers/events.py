"""
Earthquake Events Query Endpoints.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.earthquake import PaginatedEarthquakesResponse, CuratedEarthquakeOut
from app.security import get_current_user, sanitize_input_text
from app.services.earthquake_service import query_filtered_earthquakes

router = APIRouter(prefix="/api/events", tags=["Earthquake Events"])


@router.get("", response_model=PaginatedEarthquakesResponse)
async def list_events(
    start_date: Optional[datetime] = Query(None, description="Start UTC timestamp"),
    end_date: Optional[datetime] = Query(None, description="End UTC timestamp"),
    min_magnitude: Optional[float] = Query(None, description="Minimum magnitude"),
    max_magnitude: Optional[float] = Query(None, description="Maximum magnitude"),
    region: Optional[str] = Query(None, description="Filter by place name / region substring"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("time", description="Column to sort by (time, mag, depth_km)"),
    sort_order: str = Query("desc", description="asc or desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a paginated list of validated curated earthquake events matching applied filters.
    """
    safe_region = sanitize_input_text(region) if region else None

    total, items = await query_filtered_earthquakes(
        db=db,
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        region=safe_region,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }
