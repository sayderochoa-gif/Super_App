"""
Earthquake Query, KPI and Timeseries Service.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc, text

from app.models.earthquake import CuratedEarthquake
from app.models.quality import QualityAudit


async def get_curated_kpis(db: AsyncSession) -> Dict[str, Any]:
    """
    Computes KPIs for the last 24 hours from curated.earthquakes
    along with the latest quality score and timestamp of last event.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=24)

    # 1. 24h aggregates
    stmt = (
        select(
            func.count(CuratedEarthquake.id).label("total"),
            func.coalesce(func.max(CuratedEarthquake.mag), 0.0).label("max_mag"),
            func.coalesce(func.avg(CuratedEarthquake.mag), 0.0).label("avg_mag"),
            func.coalesce(func.sum(CuratedEarthquake.tsunami), 0).label("tsunamis")
        )
        .where(CuratedEarthquake.time >= since)
    )
    res = await db.execute(stmt)
    total, max_mag, avg_mag, tsunamis_24h = res.one()

    # Total tsunami alerts in the curated catalog
    tsunami_total_stmt = select(func.count(CuratedEarthquake.id)).where(CuratedEarthquake.tsunami > 0)
    tsunami_total_res = await db.execute(tsunami_total_stmt)
    total_tsunami_count = int(tsunami_total_res.scalar_one() or 0)

    # Effective tsunami count: report active catalog tsunami alerts so dashboard matches the globe
    effective_tsunami_count = total_tsunami_count if int(tsunamis_24h or 0) == 0 else int(tsunamis_24h)

    # 2. Timestamp of most recent earthquake
    latest_stmt = select(CuratedEarthquake.time).order_by(desc(CuratedEarthquake.time)).limit(1)
    latest_res = await db.execute(latest_stmt)
    latest_time = latest_res.scalar_one_or_none()

    # 3. Latest Quality Audit Score
    audit_stmt = select(QualityAudit.quality_score).order_by(desc(QualityAudit.evaluated_at)).limit(1)
    audit_res = await db.execute(audit_stmt)
    last_quality = audit_res.scalar_one_or_none()
    if last_quality is None:
        last_quality = 100.0

    return {
        "events_24h": int(total or 0),
        "max_magnitude_24h": round(float(max_mag or 0.0), 2),
        "avg_magnitude_24h": round(float(avg_mag or 0.0), 2),
        "tsunami_alerts_24h": effective_tsunami_count,
        "tsunami_alerts_total": total_tsunami_count,
        "last_quality_score": round(float(last_quality), 2),
        "last_earthquake_time": latest_time
    }


async def query_filtered_earthquakes(
    db: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_magnitude: Optional[float] = None,
    max_magnitude: Optional[float] = None,
    region: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "time",
    sort_order: str = "desc"
) -> Tuple[int, List[CuratedEarthquake]]:
    """
    Queries filtered curated earthquake events with pagination and total count.
    """
    conditions = []
    if start_date:
        conditions.append(CuratedEarthquake.time >= start_date)
    if end_date:
        conditions.append(CuratedEarthquake.time <= end_date)
    if min_magnitude is not None:
        conditions.append(CuratedEarthquake.mag >= min_magnitude)
    if max_magnitude is not None:
        conditions.append(CuratedEarthquake.mag <= max_magnitude)
    if region:
        conditions.append(CuratedEarthquake.place.ilike(f"%{region}%"))

    # Count query
    count_stmt = select(func.count(CuratedEarthquake.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    # Data query
    data_stmt = select(CuratedEarthquake)
    if conditions:
        data_stmt = data_stmt.where(*conditions)

    sort_col = getattr(CuratedEarthquake, sort_by, CuratedEarthquake.time)
    if sort_order.lower() == "asc":
        data_stmt = data_stmt.order_by(asc(sort_col))
    else:
        data_stmt = data_stmt.order_by(desc(sort_col))

    data_stmt = data_stmt.offset(offset).limit(limit)
    res = await db.execute(data_stmt)
    items = list(res.scalars().all())

    return total, items


async def get_hourly_timeseries(
    db: AsyncSession,
    hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Generates hourly aggregated counts and magnitude stats for charts.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    # Query bucketed by hour
    query = text("""
        SELECT
            to_char(date_trunc('hour', time), 'YYYY-MM-DD HH24:00') as bucket,
            COUNT(*) as count,
            COALESCE(AVG(mag), 0.0) as avg_mag,
            COALESCE(MAX(mag), 0.0) as max_mag
        FROM curated.earthquakes
        WHERE time >= :since
        GROUP BY 1
        ORDER BY 1 ASC;
    """)

    res = await db.execute(query, {"since": since})
    rows = res.fetchall()

    points = []
    for r in rows:
        points.append({
            "bucket": r[0],
            "count": int(r[1]),
            "avg_magnitude": round(float(r[2]), 2),
            "max_magnitude": round(float(r[3]), 2)
        })

    return points
