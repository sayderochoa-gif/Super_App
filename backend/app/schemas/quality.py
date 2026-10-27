"""
Quality and Quarantine Pydantic Schemas.
"""

from datetime import datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class QuarantineOut(BaseModel):
    id: int
    source_id: Optional[str] = None
    rejected_at: datetime
    reason: str
    raw_data: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class PaginatedQuarantineResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[QuarantineOut]


class QualityAuditOut(BaseModel):
    id: int
    dag_run_id: Optional[str] = None
    evaluated_at: datetime
    total_records: int
    passed_records: int
    rejected_records: int
    quality_score: float
    rules_summary: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
