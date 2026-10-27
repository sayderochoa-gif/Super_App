"""
KPIs API Endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.pipeline import KPIsResponse
from app.security import get_current_user
from app.services.earthquake_service import get_curated_kpis

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


@router.get("", response_model=KPIsResponse)
async def get_kpis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns high-level seismic indicators over the trailing 24 hours,
    including total events, maximum magnitude, average magnitude,
    active tsunami alerts, latest quality gate score, and most recent event time.
    """
    kpis = await get_curated_kpis(db)
    return kpis
