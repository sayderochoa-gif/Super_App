"""Tools for seismic data querying, statistical analysis, safe SQL execution, and sync."""

from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any, Dict, Optional
from sqlalchemy import text, func, desc
from agentebot.database.connection import get_db
from agentebot.database.models import Earthquake, Location, ImpactMetric
from agentebot.services.ingestion import ingest_usgs_feed

logger = logging.getLogger(__name__)


def sync_realtime_earthquakes(feed_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch the latest earthquake data from USGS GeoJSON feed and update the database.

    Args:
        feed_url: Optional feed URL (default: USGS hourly feed).
    """
    try:
        summary = ingest_usgs_feed(feed_url=feed_url)
        return {
            "status": "success",
            "message": "Seismic database synchronized successfully.",
            "feed_title": summary.get("feed_title"),
            "total_fetched": summary.get("total_features"),
            "new_inserted": summary.get("inserted"),
            "existing_updated": summary.get("updated"),
            "timestamp": str(summary.get("generated_at")),
        }
    except Exception as e:
        logger.error(f"Error in sync_realtime_earthquakes: {e}")
        return {
            "status": "error",
            "message": f"Failed to sync data from USGS: {str(e)}",
        }


def query_earthquakes(
    min_magnitude: Optional[float] = None,
    max_magnitude: Optional[float] = None,
    place: Optional[str] = None,
    country_or_region: Optional[str] = None,
    hours_ago: Optional[int] = None,
    tsunami_only: bool = False,
    min_sig: Optional[int] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Query earthquakes by magnitude range, geographical location, time window, and tsunami alert status.
    """
    with get_db() as db:
        query = (
            db.query(Earthquake)
            .join(Location, Earthquake.location_id == Location.id)
            .outerjoin(ImpactMetric, Earthquake.id == ImpactMetric.earthquake_id)
        )

        if min_magnitude is not None:
            query = query.filter(Earthquake.magnitude >= min_magnitude)
        if max_magnitude is not None:
            query = query.filter(Earthquake.magnitude <= max_magnitude)

        if place:
            query = query.filter(Location.place_name.ilike(f"%{place}%"))
        if country_or_region:
            query = query.filter(Location.country_or_state.ilike(f"%{country_or_region}%"))

        if hours_ago is not None and hours_ago > 0:
            since = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            query = query.filter(Earthquake.time >= since)

        if tsunami_only:
            query = query.filter(ImpactMetric.tsunami == 1)

        if min_sig is not None:
            query = query.filter(ImpactMetric.sig >= min_sig)

        query = query.order_by(desc(Earthquake.time)).limit(min(limit, 100))
        results = query.all()

        records = []
        for eq in results:
            records.append({
                "id": eq.id,
                "magnitude": eq.magnitude,
                "mag_type": eq.mag_type,
                "time": eq.time.isoformat() if eq.time else None,
                "depth_km": eq.depth_km,
                "place": eq.location.place_name if eq.location else "Unknown",
                "region": eq.location.country_or_state if eq.location else "Unknown",
                "latitude": eq.location.latitude if eq.location else None,
                "longitude": eq.location.longitude if eq.location else None,
                "tsunami_alert": bool(eq.impact_metrics.tsunami) if eq.impact_metrics else False,
                "alert_level": eq.impact_metrics.alert if eq.impact_metrics else None,
                "significance": eq.impact_metrics.sig if eq.impact_metrics else None,
                "felt_reports": eq.impact_metrics.felt if eq.impact_metrics else None,
                "url": eq.url,
            })

        return {
            "count": len(records),
            "filters_applied": {
                "min_magnitude": min_magnitude,
                "max_magnitude": max_magnitude,
                "place": place,
                "region": country_or_region,
                "hours_ago": hours_ago,
                "tsunami_only": tsunami_only,
            },
            "events": records,
        }


def get_seismic_statistics(
    hours_ago: Optional[int] = None,
    country_or_region: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive statistical metrics over the catalog:
    mean magnitude, maximum/minimum magnitude, most active seismic zones, and tsunami alerts count.
    """
    with get_db() as db:
        base_filters = []
        if hours_ago and hours_ago > 0:
            since = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            base_filters.append(Earthquake.time >= since)

        if country_or_region:
            base_filters.append(Location.country_or_state.ilike(f"%{country_or_region}%"))

        # Base aggregates
        stats_query = (
            db.query(
                func.count(Earthquake.id).label("total_events"),
                func.avg(Earthquake.magnitude).label("avg_mag"),
                func.min(Earthquake.magnitude).label("min_mag"),
                func.max(Earthquake.magnitude).label("max_mag"),
                func.avg(Earthquake.depth_km).label("avg_depth"),
            )
            .join(Location, Earthquake.location_id == Location.id)
        )
        for f in base_filters:
            stats_query = stats_query.filter(f)
        stats_row = stats_query.first()

        total_count = stats_row.total_events if stats_row else 0
        if total_count == 0:
            return {
                "total_events": 0,
                "message": "No seismic events found in the database. Run synchronization first.",
            }

        # Tsunami alerts count
        tsunami_query = (
            db.query(func.count(ImpactMetric.id))
            .join(Earthquake, ImpactMetric.earthquake_id == Earthquake.id)
            .join(Location, Earthquake.location_id == Location.id)
            .filter(ImpactMetric.tsunami == 1)
        )
        for f in base_filters:
            tsunami_query = tsunami_query.filter(f)
        tsunami_count = tsunami_query.scalar() or 0

        # Most active zones (regions)
        top_regions_query = (
            db.query(
                Location.country_or_state.label("region"),
                func.count(Earthquake.id).label("count"),
                func.max(Earthquake.magnitude).label("max_magnitude"),
            )
            .join(Earthquake, Location.id == Earthquake.location_id)
        )
        for f in base_filters:
            top_regions_query = top_regions_query.filter(f)
        top_regions = (
            top_regions_query
            .group_by(Location.country_or_state)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # Most active specific places
        top_places_query = (
            db.query(
                Location.place_name.label("place"),
                func.count(Earthquake.id).label("count"),
                func.max(Earthquake.magnitude).label("max_magnitude"),
            )
            .join(Earthquake, Location.id == Earthquake.location_id)
        )
        for f in base_filters:
            top_places_query = top_places_query.filter(f)
        top_places = (
            top_places_query
            .group_by(Location.place_name)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # Event type distribution
        types_query = (
            db.query(
                Earthquake.event_type,
                func.count(Earthquake.id).label("count"),
            )
            .join(Location, Earthquake.location_id == Location.id)
        )
        for f in base_filters:
            types_query = types_query.filter(f)
        types_breakdown = (
            types_query
            .group_by(Earthquake.event_type)
            .all()
        )

        # Strongest event
        strongest_query = (
            db.query(Earthquake)
            .join(Location, Earthquake.location_id == Location.id)
        )
        for f in base_filters:
            strongest_query = strongest_query.filter(f)
        strongest = (
            strongest_query
            .order_by(desc(Earthquake.magnitude))
            .first()
        )

        return {
            "total_events": total_count,
            "average_magnitude": round(float(stats_row.avg_mag or 0), 2),
            "min_magnitude": round(float(stats_row.min_mag or 0), 2) if stats_row.min_mag is not None else None,
            "max_magnitude": round(float(stats_row.max_mag or 0), 2) if stats_row.max_mag is not None else None,
            "average_depth_km": round(float(stats_row.avg_depth or 0), 2) if stats_row.avg_depth is not None else None,
            "tsunami_warning_events": tsunami_count,
            "strongest_event": {
                "id": strongest.id,
                "magnitude": strongest.magnitude,
                "place": strongest.location.place_name if strongest.location else None,
                "time": strongest.time.isoformat() if strongest.time else None,
            } if strongest else None,
            "top_active_regions": [
                {"region": r.region, "event_count": r.count, "max_magnitude": r.max_magnitude}
                for r in top_regions
            ],
            "top_active_places": [
                {"place": p.place, "event_count": p.count, "max_magnitude": p.max_magnitude}
                for p in top_places
            ],
            "event_types": {t.event_type: t.count for t in types_breakdown},
        }


def get_tsunami_alerts() -> Dict[str, Any]:
    """Retrieve all seismic events with active tsunami advisories or warnings."""
    return query_earthquakes(tsunami_only=True, limit=50)


def execute_safe_sql(query: str) -> Dict[str, Any]:
    """
    Execute a read-only SQL query against the normalized seismic database.
    Only SELECT statements are permitted. Mutations and DDL are strictly rejected.
    """
    clean_query = query.strip()

    # Security: Ensure only SELECT or WITH (common table expressions) queries are executed
    forbidden_keywords = [
        "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
        "REPLACE", "GRANT", "REVOKE", "ATTACH", "DETACH", "PRAGMA", "EXEC",
    ]

    # Normalize tokens and strip comments
    clean_no_comments = re.sub(r"--.*", "", clean_query)
    clean_no_comments = re.sub(r"/\*.*?\*/", "", clean_no_comments, flags=re.DOTALL)

    # Strip string literals to avoid false positives (e.g. WHERE title LIKE '%drop%')
    clean_no_strings = re.sub(r"'[^']*'", "''", clean_no_comments)

    # Prevent statement chaining via semicolon
    if ";" in clean_no_strings.strip().rstrip(";"):
        return {
            "status": "error",
            "message": "Security policy violation: Multiple statement execution is prohibited.",
        }

    tokens = clean_no_strings.split()
    first_token = tokens[0].upper() if tokens else ""

    if first_token not in ("SELECT", "WITH"):
        return {
            "status": "error",
            "message": "Security policy violation: Only SELECT queries are permitted.",
        }

    for kw in forbidden_keywords:
        pattern = rf"\b{kw}\b"
        if re.search(pattern, clean_no_strings, re.IGNORECASE):
            return {
                "status": "error",
                "message": f"Security policy violation: Forbidden keyword '{kw}' detected.",
            }

    # Enforce safe row limit if not specified
    if not re.search(r"\bLIMIT\s+\d+", clean_no_strings, re.IGNORECASE):
        clean_query = f"{clean_query.rstrip(';')} LIMIT 50"

    with get_db() as db:
        try:
            result = db.execute(text(clean_query))
            keys = list(result.keys())
            raw_rows = result.fetchall()

            rows = []
            for row in raw_rows:
                row_dict = {}
                for idx, col in enumerate(keys):
                    val = row[idx]
                    if isinstance(val, datetime):
                        val = val.isoformat()
                    row_dict[col] = val
                rows.append(row_dict)

            return {
                "status": "success",
                "columns": keys,
                "row_count": len(rows),
                "data": rows,
                "executed_query": clean_query,
            }
        except Exception as e:
            logger.error(f"SQL execution error for '{clean_query}': {e}")
            return {
                "status": "error",
                "message": f"SQL execution error: {str(e)}",
                "executed_query": clean_query,
            }


def get_database_schema() -> str:
    """Return the schema definition of the relational tables for LLM SQL generation."""
    return """
TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_name VARCHAR(255) NOT NULL,    -- Detailed place descriptor e.g. '10 km NE of Pahala, Hawaii'
    country_or_state VARCHAR(100),       -- Extracted region/state/country e.g. 'Hawaii', 'California'
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    created_at TIMESTAMP
);

TABLE earthquakes (
    id VARCHAR(64) PRIMARY KEY,          -- USGS Event ID e.g. 'ci41353591'
    location_id INTEGER REFERENCES locations(id),
    magnitude FLOAT,                     -- Richter / moment magnitude
    mag_type VARCHAR(16),                -- e.g. 'ml', 'md', 'mw'
    time TIMESTAMP NOT NULL,             -- Event occurrence time (UTC)
    updated TIMESTAMP,                   -- Last update time (UTC)
    depth_km FLOAT,                      -- Depth in kilometers
    event_type VARCHAR(32),              -- 'earthquake', 'quarry blast', etc.
    title VARCHAR(255),                  -- Event title e.g. 'M 1.8 - 11 km E of Yorba Linda, CA'
    url VARCHAR(512),                    -- USGS event web page
    created_at TIMESTAMP
);

TABLE impact_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    earthquake_id VARCHAR(64) UNIQUE REFERENCES earthquakes(id),
    felt INTEGER,                        -- Number of community felt reports
    cdi FLOAT,                           -- Community Decimal Intensity
    mmi FLOAT,                           -- Modified Mercalli Intensity
    alert VARCHAR(16),                   -- PAGER alert: 'green', 'yellow', 'orange', 'red'
    tsunami INTEGER,                     -- 1 if tsunami advisory/warning issued, 0 otherwise
    sig INTEGER,                         -- Event significance score (0 to 1000)
    status VARCHAR(32),                  -- 'reviewed' or 'automatic'
    nst INTEGER,                         -- Number of seismic stations
    dmin FLOAT,                          -- Distance to closest station (degrees)
    rms FLOAT,                           -- Travel time residual (seconds)
    gap FLOAT,                           -- Azimuthal gap (degrees)
    net VARCHAR(16),                     -- Contributing seismic network code
    code VARCHAR(32)
);
"""


# Function schemas for LLM Tool Calling (OpenAI spec)
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sync_realtime_earthquakes",
            "description": "Fetch real-time seismic data from the USGS GeoJSON feed and update the relational database with upsert logic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feed_url": {
                        "type": "string",
                        "description": "Optional custom USGS GeoJSON URL or feed shortcut ('all_hour', 'all_day', 'all_week').",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_earthquakes",
            "description": "Search earthquakes using filters like minimum/maximum magnitude, geographical region or place, time range, and tsunami alert status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_magnitude": {
                        "type": "number",
                        "description": "Minimum earthquake magnitude (e.g. 2.5, 4.0, 5.0).",
                    },
                    "max_magnitude": {
                        "type": "number",
                        "description": "Maximum earthquake magnitude.",
                    },
                    "place": {
                        "type": "string",
                        "description": "Text filter for location place name (e.g. 'California', 'Pahala', 'Alaska').",
                    },
                    "country_or_region": {
                        "type": "string",
                        "description": "Region, country, or state name (e.g. 'CA', 'Hawaii', 'Chile', 'Japan').",
                    },
                    "hours_ago": {
                        "type": "integer",
                        "description": "Lookback time window in hours (e.g. 1, 6, 24).",
                    },
                    "tsunami_only": {
                        "type": "boolean",
                        "description": "If true, returns only events that triggered a tsunami advisory/warning.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of events to return (default 20).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_seismic_statistics",
            "description": "Get high-level statistical aggregations of seismic activity, including total count, average magnitude, strongest earthquake, top active regions, and tsunami alert metrics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "hours_ago": {
                        "type": "integer",
                        "description": "Optional filter for events in the last N hours.",
                    },
                    "country_or_region": {
                        "type": "string",
                        "description": "Optional region/state filter for focused statistics.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tsunami_alerts",
            "description": "Retrieve all recent seismic events that have triggered a tsunami warning or advisory.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_safe_sql",
            "description": "Execute a secure, read-only SELECT query against the normalized SQLite/PostgreSQL database to answer complex analytical questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The read-only SQL query to execute. Must be a SELECT statement. Tables: 'locations', 'earthquakes', 'impact_metrics'.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

# Map tool names to python callables
TOOL_DISPATCHER = {
    "sync_realtime_earthquakes": sync_realtime_earthquakes,
    "query_earthquakes": query_earthquakes,
    "get_seismic_statistics": get_seismic_statistics,
    "get_tsunami_alerts": get_tsunami_alerts,
    "execute_safe_sql": execute_safe_sql,
}
