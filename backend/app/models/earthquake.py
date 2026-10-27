"""
Earthquake Models for Raw, Staging, and Curated Lakehouse Schemas.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, JSON
from app.database import Base


class RawEarthquakeFeed(Base):
    __tablename__ = "earthquake_feeds"
    __table_args__ = {"schema": "raw"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    source = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)


class StagingEarthquake(Base):
    __tablename__ = "earthquakes"
    __table_args__ = {"schema": "staging"}

    id = Column(String(100), primary_key=True)
    mag = Column(Float, nullable=True)
    place = Column(Text, nullable=True)
    time = Column(DateTime(timezone=True), nullable=True)
    updated = Column(DateTime(timezone=True), nullable=True)
    tz = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    detail = Column(Text, nullable=True)
    felt = Column(Integer, nullable=True)
    cdi = Column(Float, nullable=True)
    mmi = Column(Float, nullable=True)
    alert = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    tsunami = Column(Integer, default=0)
    sig = Column(Integer, nullable=True)
    net = Column(String(50), nullable=True)
    code = Column(String(50), nullable=True)
    ids = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)
    types = Column(Text, nullable=True)
    nst = Column(Integer, nullable=True)
    dmin = Column(Float, nullable=True)
    rms = Column(Float, nullable=True)
    gap = Column(Float, nullable=True)
    magType = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)
    title = Column(Text, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    depth_km = Column(Float, nullable=True)
    processed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CuratedEarthquake(Base):
    __tablename__ = "earthquakes"
    __table_args__ = {"schema": "curated"}

    id = Column(String(100), primary_key=True)
    mag = Column(Float, nullable=False, index=True)
    place = Column(Text, nullable=True)
    time = Column(DateTime(timezone=True), nullable=False, index=True)
    updated = Column(DateTime(timezone=True), nullable=True)
    tz = Column(Integer, nullable=True)
    url = Column(Text, nullable=True)
    detail = Column(Text, nullable=True)
    felt = Column(Integer, nullable=True)
    cdi = Column(Float, nullable=True)
    mmi = Column(Float, nullable=True)
    alert = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    tsunami = Column(Integer, default=0)
    sig = Column(Integer, nullable=True)
    net = Column(String(50), nullable=True)
    code = Column(String(50), nullable=True)
    ids = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)
    types = Column(Text, nullable=True)
    nst = Column(Integer, nullable=True)
    dmin = Column(Float, nullable=True)
    rms = Column(Float, nullable=True)
    gap = Column(Float, nullable=True)
    magType = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)
    title = Column(Text, nullable=True)
    longitude = Column(Float, nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    depth_km = Column(Float, nullable=False)
    curated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
