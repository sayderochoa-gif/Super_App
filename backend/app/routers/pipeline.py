"""
Pipeline Health and Data Quality Monitoring Endpoints.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User
from app.models.quality import QualityAudit
from app.models.earthquake import CuratedEarthquake
from app.schemas.pipeline import PipelineStatusResponse
from app.schemas.quality import QualityAuditOut
from app.security import get_current_user
from app.services.airflow_service import get_airflow_dag_status

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline & Quality Monitoring"])


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns pipeline health, including DAG execution states,
    latest quality gate audit, and current data freshness.
    """
    # 1. Fetch Airflow DAG statuses
    dag_ids = [
        "dag_ingestion_realtime",
        "dag_transformation_quality",
        "dag_ai_daily_report",
        "dag_backfill_historical"
    ]
    dag_statuses = {}
    for did in dag_ids:
        dag_statuses[did] = await get_airflow_dag_status(did)

    # 2. Fetch Latest Quality Audit
    audit_stmt = select(QualityAudit).order_by(desc(QualityAudit.evaluated_at)).limit(1)
    audit_res = await db.execute(audit_stmt)
    latest_audit = audit_res.scalar_one_or_none()

    audit_dict = None
    if latest_audit:
        audit_dict = {
            "id": latest_audit.id,
            "evaluated_at": latest_audit.evaluated_at.isoformat(),
            "quality_score": latest_audit.quality_score,
            "total_records": latest_audit.total_records,
            "passed_records": latest_audit.passed_records,
            "rejected_records": latest_audit.rejected_records,
            "rules_summary": latest_audit.rules_summary
        }

    # 3. Data Freshness
    event_stmt = select(CuratedEarthquake.time).order_by(desc(CuratedEarthquake.time)).limit(1)
    event_res = await db.execute(event_stmt)
    last_event_time = event_res.scalar_one_or_none()

    data_freshness_hours = None
    is_fresh = True
    if last_event_time:
        now = datetime.now(timezone.utc)
        diff = (now - last_event_time).total_seconds() / 3600.0
        data_freshness_hours = round(diff, 2)
        is_fresh = diff <= 6.0

    return {
        "dag_statuses": dag_statuses,
        "data_freshness_hours": data_freshness_hours,
        "is_fresh": is_fresh,
        "latest_quality_audit": audit_dict,
        "last_event_time": last_event_time
    }


@router.get("/quality-history", response_model=List[QualityAuditOut])
async def get_quality_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns recent quality evaluation audit runs."""
    stmt = select(QualityAudit).order_by(desc(QualityAudit.evaluated_at)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())
