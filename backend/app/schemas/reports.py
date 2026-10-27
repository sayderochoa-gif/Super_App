"""
AI Reports Pydantic Schemas.
"""

from datetime import date, datetime
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict


class AIDailyReportOut(BaseModel):
    id: int
    report_date: date
    narrative_text: str
    structured_kpis: Dict[str, Any]
    model_name: str
    tokens_used: int
    latency_sec: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAnomalyOut(BaseModel):
    id: int
    detected_at: datetime
    anomaly_type: str
    metric_trigger: str
    description: str
    event_ids: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)
