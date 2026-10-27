"""
Quality Assurance and Quarantine Database Models.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON
from app.database import Base


class QuarantineEvent(Base):
    __tablename__ = "quarantine"
    __table_args__ = {"schema": "curated"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(100), nullable=True, index=True)
    rejected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    reason = Column(Text, nullable=False)
    raw_data = Column(JSON, nullable=False)


class QualityAudit(Base):
    __tablename__ = "quality_audit"
    __table_args__ = {"schema": "curated"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    dag_run_id = Column(String(255), nullable=True)
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    total_records = Column(Integer, nullable=False)
    passed_records = Column(Integer, nullable=False)
    rejected_records = Column(Integer, nullable=False)
    quality_score = Column(Float, nullable=False)
    rules_summary = Column(JSON, nullable=False)
