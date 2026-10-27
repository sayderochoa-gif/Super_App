"""
Pipeline, KPI, and Timeseries Schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class KPIsResponse(BaseModel):
    events_24h: int
    max_magnitude_24h: float
    avg_magnitude_24h: float
    tsunami_alerts_24h: int
    last_quality_score: float
    last_earthquake_time: Optional[datetime] = None


class TimeseriesPoint(BaseModel):
    bucket: str
    count: int
    avg_magnitude: float
    max_magnitude: float


class TimeseriesResponse(BaseModel):
    data: List[TimeseriesPoint]


class PipelineStatusResponse(BaseModel):
    dag_statuses: Dict[str, Any]
    data_freshness_hours: Optional[float]
    is_fresh: bool
    latest_quality_audit: Optional[Dict[str, Any]]
    last_event_time: Optional[datetime]


class BackfillRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    min_mag: float = 2.5


class ActionResponse(BaseModel):
    status: str
    message: str
    execution_info: Optional[Dict[str, Any]] = None
