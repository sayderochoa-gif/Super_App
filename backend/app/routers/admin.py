"""
Admin-Only Management and Quarantine Inspection Endpoints.
Guarded strictly by RBAC (role: 'admin').
Viewers attempting access receive HTTP 403 Forbidden.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models.user import User
from app.models.quality import QuarantineEvent
from app.schemas.quality import PaginatedQuarantineResponse
from app.schemas.pipeline import BackfillRequest, ActionResponse
from app.security import require_role
from app.services.airflow_service import trigger_airflow_dag

router = APIRouter(tags=["Admin Operations"])


@router.get("/api/quality/quarantine", response_model=PaginatedQuarantineResponse)
async def list_quarantined_records(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns quarantined records with validation failure details.
    Accessible ONLY to users with 'admin' role. Viewers receive 403 Forbidden.
    """
    count_stmt = select(func.count(QuarantineEvent.id))
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    data_stmt = (
        select(QuarantineEvent)
        .order_by(desc(QuarantineEvent.rejected_at))
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(data_stmt)
    items = list(res.scalars().all())

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@router.post("/api/admin/backfill", response_model=ActionResponse)
async def trigger_backfill(
    request: BackfillRequest,
    admin_user: User = Depends(require_role(["admin"]))
):
    """
    Triggers the Airflow historical backfill DAG for a parameterized window.
    Accessible ONLY to 'admin' role.
    """
    conf = {
        "start_date": request.start_date,
        "end_date": request.end_date,
        "min_mag": request.min_mag
    }

    result = await trigger_airflow_dag("dag_backfill_historical", conf=conf)
    return {
        "status": "success",
        "message": f"Historical backfill triggered for range {request.start_date} to {request.end_date} (Min Mag: {request.min_mag}).",
        "execution_info": result
    }


@router.post("/api/admin/reports/regenerate", response_model=ActionResponse)
async def trigger_report_regeneration(
    admin_user: User = Depends(require_role(["admin"]))
):
    """
    Forces immediate execution of the AI daily report generation DAG in Airflow.
    Accessible ONLY to 'admin' role.
    """
    result = await trigger_airflow_dag("dag_ai_daily_report")
    return {
        "status": "success",
        "message": "AI daily report regeneration task triggered successfully.",
        "execution_info": result
    }
