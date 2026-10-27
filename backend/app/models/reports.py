"""
AI Reports and Anomaly Database Models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, Date, DateTime, JSON
from app.database import Base


class AIDailyReport(Base):
    __tablename__ = "ai_daily_reports"
    __table_args__ = {"schema": "curated"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(Date, unique=True, nullable=False, index=True)
    narrative_text = Column(Text, nullable=False)
    structured_kpis = Column(JSON, nullable=False)
    model_name = Column(String(100), nullable=False)
    tokens_used = Column(Integer, default=0)
    latency_sec = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AIAnomaly(Base):
    __tablename__ = "ai_anomalies"
    __table_args__ = {"schema": "curated"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    anomaly_type = Column(String(100), nullable=False, index=True)
    metric_trigger = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    event_ids = Column(JSON, nullable=True)
