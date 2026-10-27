"""
SismoWatch Data Quality Engine.
Provides schema validation, data flattening, volume/freshness checks,
and quarantine routing using Pandera and Pandas.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import pandera as pa
from pandera import Column, Check, DataFrameSchema


def parse_epoch_ms(val: Any) -> datetime | None:
    """Safely converts millisecond epoch integer or float to UTC datetime."""
    if val is None or pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val / 1000.0, tz=timezone.utc)
        if isinstance(val, str):
            # Try float/int conversion or ISO string
            try:
                num = float(val)
                return datetime.fromtimestamp(num / 1000.0, tz=timezone.utc)
            except ValueError:
                dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=timezone.utc)
            return val
    except Exception:
        return None
    return None


def flatten_geojson_features(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Flattens a list of USGS GeoJSON feature dicts into tabular dictionary format
    matching staging.earthquakes schema.
    """
    flattened = []
    for feat in features:
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or [None, None, None]

        lon = coords[0] if len(coords) > 0 else None
        lat = coords[1] if len(coords) > 1 else None
        depth = coords[2] if len(coords) > 2 else None

        flattened.append({
            "id": feat.get("id"),
            "mag": float(props["mag"]) if props.get("mag") is not None and not pd.isna(props.get("mag")) else None,
            "place": props.get("place"),
            "time": parse_epoch_ms(props.get("time")),
            "updated": parse_epoch_ms(props.get("updated")),
            "tz": props.get("tz"),
            "url": props.get("url"),
            "detail": props.get("detail"),
            "felt": props.get("felt"),
            "cdi": float(props["cdi"]) if props.get("cdi") is not None and not pd.isna(props.get("cdi")) else None,
            "mmi": float(props["mmi"]) if props.get("mmi") is not None and not pd.isna(props.get("mmi")) else None,
            "alert": props.get("alert"),
            "status": props.get("status"),
            "tsunami": int(props["tsunami"]) if props.get("tsunami") is not None else 0,
            "sig": int(props["sig"]) if props.get("sig") is not None else None,
            "net": props.get("net"),
            "code": props.get("code"),
            "ids": props.get("ids"),
            "sources": props.get("sources"),
            "types": props.get("types"),
            "nst": props.get("nst"),
            "dmin": float(props["dmin"]) if props.get("dmin") is not None and not pd.isna(props.get("dmin")) else None,
            "rms": float(props["rms"]) if props.get("rms") is not None and not pd.isna(props.get("rms")) else None,
            "gap": float(props["gap"]) if props.get("gap") is not None and not pd.isna(props.get("gap")) else None,
            "magType": props.get("magType"),
            "type": props.get("type"),
            "title": props.get("title"),
            "longitude": float(lon) if lon is not None and not pd.isna(lon) else None,
            "latitude": float(lat) if lat is not None and not pd.isna(lat) else None,
            "depth_km": float(depth) if depth is not None and not pd.isna(depth) else None,
            "_raw": feat  # preserved for quarantine traceability
        })
    return flattened


# Pandera Schema Specification for Curated Quality Gate
CuratedEarthquakeSchema = DataFrameSchema(
    {
        "id": Column(
            str,
            Check(lambda s: s.str.strip().str.len() > 0, error="id must not be empty"),
            nullable=False,
            required=True
        ),
        "mag": Column(
            float,
            Check.in_range(-2.0, 10.0, include_min=True, include_max=True),
            nullable=False,
            required=True
        ),
        "latitude": Column(
            float,
            Check.in_range(-90.0, 90.0, include_min=True, include_max=True),
            nullable=False,
            required=True
        ),
        "longitude": Column(
            float,
            Check.in_range(-180.0, 180.0, include_min=True, include_max=True),
            nullable=False,
            required=True
        ),
        "depth_km": Column(
            float,
            Check.in_range(-5.0, 1000.0, include_min=True, include_max=True),
            nullable=False,
            required=True
        ),
        "time": Column(
            pa.DateTime,
            nullable=False,
            required=True
        )
    },
    coerce=False,
    strict=False
)


def validate_single_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Performs field-level validation and produces human-readable, specific rejection reasons.
    """
    reasons = []
    
    # 1. ID Check
    rec_id = record.get("id")
    if not rec_id or not isinstance(rec_id, str) or len(rec_id.strip()) == 0:
        reasons.append("Invalid or missing 'id'")

    # 2. Time Check
    rec_time = record.get("time")
    if rec_time is None or pd.isna(rec_time):
        reasons.append("Missing or unparseable 'time'")
    else:
        # Time shouldn't be in future (margin 10 mins for clock drift)
        now_utc = datetime.now(timezone.utc)
        if isinstance(rec_time, datetime):
            comp_time = rec_time if rec_time.tzinfo else rec_time.replace(tzinfo=timezone.utc)
            if comp_time > (now_utc + timedelta(minutes=10)):
                reasons.append(f"Event time is in future: {comp_time.isoformat()} > {now_utc.isoformat()}")

    # 3. Magnitude Check
    mag = record.get("mag")
    if mag is None or pd.isna(mag):
        reasons.append("Missing 'mag' value")
    else:
        try:
            val_mag = float(mag)
            if val_mag < -2.0 or val_mag > 10.0:
                reasons.append(f"Magnitude {val_mag} outside plausible range [-2.0, 10.0]")
        except (ValueError, TypeError):
            reasons.append(f"Non-numeric magnitude: {mag}")

    # 4. Latitude Check
    lat = record.get("latitude")
    if lat is None or pd.isna(lat):
        reasons.append("Missing 'latitude' coordinate")
    else:
        try:
            val_lat = float(lat)
            if val_lat < -90.0 or val_lat > 90.0:
                reasons.append(f"Latitude {val_lat} outside valid bounds [-90.0, 90.0]")
        except (ValueError, TypeError):
            reasons.append(f"Non-numeric latitude: {lat}")

    # 5. Longitude Check
    lon = record.get("longitude")
    if lon is None or pd.isna(lon):
        reasons.append("Missing 'longitude' coordinate")
    else:
        try:
            val_lon = float(lon)
            if val_lon < -180.0 or val_lon > 180.0:
                reasons.append(f"Longitude {val_lon} outside valid bounds [-180.0, 180.0]")
        except (ValueError, TypeError):
            reasons.append(f"Non-numeric longitude: {lon}")

    # 6. Depth Check
    depth = record.get("depth_km")
    if depth is None or pd.isna(depth):
        reasons.append("Missing 'depth_km'")
    else:
        try:
            val_depth = float(depth)
            if val_depth < -5.0 or val_depth > 1000.0:
                reasons.append(f"Depth {val_depth} km outside plausible range [-5.0, 1000.0]")
        except (ValueError, TypeError):
            reasons.append(f"Non-numeric depth: {depth}")

    return (len(reasons) == 0, reasons)


def evaluate_batch_quality(
    records: List[Dict[str, Any]],
    dag_run_id: str = "manual_execution"
) -> Dict[str, Any]:
    """
    Applies the Quality Gate to a batch of flattened earthquake records.
    Returns:
        - passed_records: list of clean dicts ready for curated.earthquakes
        - quarantine_records: list of rejected entries for curated.quarantine
        - audit_summary: metadata dict for curated.quality_audit
    """
    total = len(records)
    if total == 0:
        return {
            "passed_records": [],
            "quarantine_records": [],
            "audit_summary": {
                "dag_run_id": dag_run_id,
                "evaluated_at": datetime.now(timezone.utc),
                "total_records": 0,
                "passed_records": 0,
                "rejected_records": 0,
                "quality_score": 100.0,
                "rules_summary": {"status": "empty_feed", "passed": 0, "rejected": 0}
            }
        }

    passed = []
    quarantine = []
    rules_counter = {
        "id_check": 0,
        "time_check": 0,
        "mag_check": 0,
        "lat_check": 0,
        "lon_check": 0,
        "depth_check": 0
    }

    now_utc = datetime.now(timezone.utc)

    for rec in records:
        is_valid, reasons = validate_single_record(rec)
        raw_payload = rec.get("_raw") or {k: (str(v) if isinstance(v, datetime) else v) for k, v in rec.items() if k != "_raw"}

        if is_valid:
            # Clean record for insertion, remove internal tracing
            clean_rec = {k: v for k, v in rec.items() if k != "_raw"}
            passed.append(clean_rec)
        else:
            for r in reasons:
                if "id" in r:
                    rules_counter["id_check"] += 1
                if "time" in r:
                    rules_counter["time_check"] += 1
                if "mag" in r or "Magnitude" in r:
                    rules_counter["mag_check"] += 1
                if "latitude" in r or "Latitude" in r:
                    rules_counter["lat_check"] += 1
                if "longitude" in r or "Longitude" in r:
                    rules_counter["lon_check"] += 1
                if "depth" in r or "Depth" in r:
                    rules_counter["depth_check"] += 1

            quarantine.append({
                "source_id": str(rec.get("id") or "UNKNOWN"),
                "rejected_at": now_utc,
                "reason": " | ".join(reasons),
                "raw_data": raw_payload
            })

    passed_count = len(passed)
    rejected_count = len(quarantine)
    quality_score = round((passed_count / total) * 100.0, 2) if total > 0 else 100.0

    audit_summary = {
        "dag_run_id": dag_run_id,
        "evaluated_at": now_utc,
        "total_records": total,
        "passed_records": passed_count,
        "rejected_records": rejected_count,
        "quality_score": quality_score,
        "rules_summary": {
            "failures_by_rule": rules_counter,
            "acceptance_ratio": quality_score
        }
    }

    return {
        "passed_records": passed,
        "quarantine_records": quarantine,
        "audit_summary": audit_summary
    }


def check_feed_freshness(latest_record_time: datetime | None, threshold_hours: float = 6.0) -> Dict[str, Any]:
    """
    Checks if the most recent event in the batch conforms to freshness requirements.
    """
    if latest_record_time is None:
        return {"fresh": False, "delta_hours": None, "warning": "No events available to evaluate freshness."}

    now = datetime.now(timezone.utc)
    target = latest_record_time if latest_record_time.tzinfo else latest_record_time.replace(tzinfo=timezone.utc)
    delta_hours = (now - target).total_seconds() / 3600.0

    is_fresh = delta_hours <= threshold_hours
    return {
        "fresh": is_fresh,
        "delta_hours": round(delta_hours, 2),
        "warning": None if is_fresh else f"Feed freshness alert: latest record is {delta_hours:.1f} hours old (threshold: {threshold_hours}h)"
    }
