"""SQLAlchemy relational models for seismic telemetry and impact analysis."""

from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from agentebot.database.connection import Base


class Location(Base):
    """Normalized geographic locations associated with seismic events."""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    place_name = Column(String(255), nullable=False, index=True)
    country_or_state = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    earthquakes = relationship(
        "Earthquake",
        back_populates="location",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_locations_lat_lon", "latitude", "longitude"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "place_name": self.place_name,
            "country_or_state": self.country_or_state,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Location id={self.id} place='{self.place_name}' lat={self.latitude} lon={self.longitude}>"


class Earthquake(Base):
    """Core seismic event entity cataloged by USGS."""

    __tablename__ = "earthquakes"

    id = Column(String(64), primary_key=True, index=True)  # USGS Feature ID
    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    magnitude = Column(Float, nullable=True, index=True)
    mag_type = Column(String(16), nullable=True)
    time = Column(DateTime(timezone=True), nullable=False, index=True)
    updated = Column(DateTime(timezone=True), nullable=True)
    depth_km = Column(Float, nullable=True)
    event_type = Column(String(32), default="earthquake", index=True)
    title = Column(String(255), nullable=True)
    url = Column(String(512), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    location = relationship("Location", back_populates="earthquakes")
    impact_metrics = relationship(
        "ImpactMetric",
        back_populates="earthquake",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_earthquakes_time_mag", "time", "magnitude"),
    )

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "magnitude": self.magnitude,
            "mag_type": self.mag_type,
            "time": self.time.isoformat() if self.time else None,
            "depth_km": self.depth_km,
            "event_type": self.event_type,
            "title": self.title,
            "url": self.url,
            "location": self.location.to_dict() if self.location else None,
        }
        if self.impact_metrics:
            data["impact"] = self.impact_metrics.to_dict()
        return data

    def __repr__(self) -> str:
        return f"<Earthquake id='{self.id}' mag={self.magnitude} time='{self.time}'>"


class ImpactMetric(Base):
    """Normalized metrics, community reports, and severity alerts for an event."""

    __tablename__ = "impact_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    earthquake_id = Column(
        String(64),
        ForeignKey("earthquakes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    felt = Column(Integer, nullable=True)  # Felt reports count
    cdi = Column(Float, nullable=True)    # Community Decimal Intensity
    mmi = Column(Float, nullable=True)    # Modified Mercalli Intensity
    alert = Column(String(16), nullable=True)  # PAGER alert level ('green', 'yellow', etc.)
    tsunami = Column(Integer, default=0, index=True)  # 0: None, 1: Tsunami Warning/Advisory
    sig = Column(Integer, nullable=True, index=True)  # Event Significance (0 - 1000)
    status = Column(String(32), default="automatic")  # 'reviewed' or 'automatic'
    nst = Column(Integer, nullable=True)  # Number of seismic stations used
    dmin = Column(Float, nullable=True)   # Horizontal distance to nearest station
    rms = Column(Float, nullable=True)    # RMS travel time residual
    gap = Column(Float, nullable=True)    # Azimuthal gap
    net = Column(String(16), nullable=True)  # Network contributor code
    code = Column(String(32), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    earthquake = relationship("Earthquake", back_populates="impact_metrics")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "felt": self.felt,
            "cdi": self.cdi,
            "mmi": self.mmi,
            "alert": self.alert,
            "tsunami": self.tsunami,
            "sig": self.sig,
            "status": self.status,
            "nst": self.nst,
            "dmin": self.dmin,
            "rms": self.rms,
            "gap": self.gap,
            "net": self.net,
            "code": self.code,
        }

    def __repr__(self) -> str:
        return f"<ImpactMetric eq_id='{self.earthquake_id}' tsunami={self.tsunami} sig={self.sig}>"
