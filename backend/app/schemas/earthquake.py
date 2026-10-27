"""
Earthquake Pydantic Schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class CuratedEarthquakeOut(BaseModel):
    id: str
    mag: float
    place: Optional[str] = None
    time: datetime
    updated: Optional[datetime] = None
    tz: Optional[int] = None
    url: Optional[str] = None
    detail: Optional[str] = None
    felt: Optional[int] = None
    cdi: Optional[float] = None
    mmi: Optional[float] = None
    alert: Optional[str] = None
    status: Optional[str] = None
    tsunami: int = 0
    sig: Optional[int] = None
    net: Optional[str] = None
    code: Optional[str] = None
    ids: Optional[str] = None
    sources: Optional[str] = None
    types: Optional[str] = None
    nst: Optional[int] = None
    dmin: Optional[float] = None
    rms: Optional[float] = None
    gap: Optional[float] = None
    magType: Optional[str] = None
    type: Optional[str] = None
    title: Optional[str] = None
    longitude: float
    latitude: float
    depth_km: float
    curated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedEarthquakesResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[CuratedEarthquakeOut]
