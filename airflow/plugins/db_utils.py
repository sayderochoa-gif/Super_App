"""
Database Utility Module for Airflow DAGs.
Supports connection pooling, idempotent UPSERTs into raw, staging, and curated layers.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import execute_values, Json

logger = logging.getLogger("sismowatch.db_utils")


def get_db_connection():
    """
    Retrieves a Postgres connection using environment variables.
    Works inside Docker Compose and standalone execution.
    """
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return psycopg2.connect(db_url)

    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = int(os.environ.get("POSTGRES_PORT", 5432))
    database = os.environ.get("POSTGRES_DB", "sismowatch")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres_master_pass")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password
    )


def insert_raw_feed(source: str, payload: Dict[str, Any]) -> int:
    """Inserts a raw JSON feed payload into raw.earthquake_feeds and returns feed id."""
    sql = """
        INSERT INTO raw.earthquake_feeds (source, payload, ingested_at)
        VALUES (%s, %s, NOW())
        RETURNING id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (source, Json(payload)))
            feed_id = cur.fetchone()[0]
            conn.commit()
            return feed_id


def get_latest_raw_feed() -> Optional[Dict[str, Any]]:
    """Retrieves the most recent raw feed entry."""
    sql = """
        SELECT id, source, payload, ingested_at
        FROM raw.earthquake_feeds
        ORDER BY id DESC
        LIMIT 1;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "source": row[1],
                "payload": row[2],
                "ingested_at": row[3]
            }


def upsert_staging_earthquakes(records: List[Dict[str, Any]]) -> int:
    """
    Idempotent UPSERT into staging.earthquakes based on primary key 'id'.
    """
    if not records:
        return 0

    cols = [
        "id", "mag", "place", "time", "updated", "tz", "url", "detail", "felt",
        "cdi", "mmi", "alert", "status", "tsunami", "sig", "net", "code", "ids",
        "sources", "types", "nst", "dmin", "rms", "gap", "magType", "type",
        "title", "longitude", "latitude", "depth_km"
    ]

    sql = f"""
        INSERT INTO staging.earthquakes ({', '.join(cols)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            mag = EXCLUDED.mag,
            place = EXCLUDED.place,
            time = EXCLUDED.time,
            updated = EXCLUDED.updated,
            status = EXCLUDED.status,
            tsunami = EXCLUDED.tsunami,
            sig = EXCLUDED.sig,
            detail = EXCLUDED.detail,
            felt = EXCLUDED.felt,
            cdi = EXCLUDED.cdi,
            mmi = EXCLUDED.mmi,
            alert = EXCLUDED.alert,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            depth_km = EXCLUDED.depth_km,
            processed_at = NOW();
    """

    data_tuples = []
    for r in records:
        data_tuples.append(tuple(r.get(c) for c in cols))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, data_tuples)
            conn.commit()
            return len(records)


def upsert_curated_earthquakes(records: List[Dict[str, Any]]) -> int:
    """
    Idempotent UPSERT into curated.earthquakes based on primary key 'id'.
    """
    if not records:
        return 0

    cols = [
        "id", "mag", "place", "time", "updated", "tz", "url", "detail", "felt",
        "cdi", "mmi", "alert", "status", "tsunami", "sig", "net", "code", "ids",
        "sources", "types", "nst", "dmin", "rms", "gap", "magType", "type",
        "title", "longitude", "latitude", "depth_km"
    ]

    sql = f"""
        INSERT INTO curated.earthquakes ({', '.join(cols)})
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            mag = EXCLUDED.mag,
            place = EXCLUDED.place,
            time = EXCLUDED.time,
            updated = EXCLUDED.updated,
            status = EXCLUDED.status,
            tsunami = EXCLUDED.tsunami,
            sig = EXCLUDED.sig,
            detail = EXCLUDED.detail,
            felt = EXCLUDED.felt,
            cdi = EXCLUDED.cdi,
            mmi = EXCLUDED.mmi,
            alert = EXCLUDED.alert,
            longitude = EXCLUDED.longitude,
            latitude = EXCLUDED.latitude,
            depth_km = EXCLUDED.depth_km,
            curated_at = NOW();
    """

    data_tuples = []
    for r in records:
        data_tuples.append(tuple(r.get(c) for c in cols))

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, data_tuples)
            conn.commit()
            return len(records)


def insert_quarantine_records(records: List[Dict[str, Any]]) -> int:
    """Inserts rejected records into curated.quarantine."""
    if not records:
        return 0

    sql = """
        INSERT INTO curated.quarantine (source_id, reason, raw_data, rejected_at)
        VALUES %s;
    """
    data = [
        (r.get("source_id"), r.get("reason"), Json(r.get("raw_data")), r.get("rejected_at"))
        for r in records
    ]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, data)
            conn.commit()
            return len(records)


def insert_quality_audit(audit: Dict[str, Any]) -> int:
    """Inserts an evaluation record into curated.quality_audit."""
    sql = """
        INSERT INTO curated.quality_audit (
            dag_run_id, evaluated_at, total_records, passed_records,
            rejected_records, quality_score, rules_summary
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    audit.get("dag_run_id"),
                    audit.get("evaluated_at"),
                    audit.get("total_records"),
                    audit.get("passed_records"),
                    audit.get("rejected_records"),
                    audit.get("quality_score"),
                    Json(audit.get("rules_summary"))
                )
            )
            aid = cur.fetchone()[0]
            conn.commit()
            return aid


def upsert_ai_daily_report(report: Dict[str, Any]) -> int:
    """Idempotent UPSERT into curated.ai_daily_reports by report_date."""
    sql = """
        INSERT INTO curated.ai_daily_reports (
            report_date, narrative_text, structured_kpis, model_name,
            tokens_used, latency_sec, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (report_date) DO UPDATE SET
            narrative_text = EXCLUDED.narrative_text,
            structured_kpis = EXCLUDED.structured_kpis,
            model_name = EXCLUDED.model_name,
            tokens_used = EXCLUDED.tokens_used,
            latency_sec = EXCLUDED.latency_sec,
            created_at = NOW()
        RETURNING id;
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql,
                (
                    report["report_date"],
                    report["narrative_text"],
                    Json(report["structured_kpis"]),
                    report["model_name"],
                    report["tokens_used"],
                    report["latency_sec"]
                )
            )
            rid = cur.fetchone()[0]
            conn.commit()
            return rid


def insert_ai_anomalies(anomalies: List[Dict[str, Any]]) -> int:
    """Inserts detected anomalies into curated.ai_anomalies."""
    if not anomalies:
        return 0

    sql = """
        INSERT INTO curated.ai_anomalies (
            detected_at, anomaly_type, metric_trigger, description, event_ids
        ) VALUES %s;
    """
    data = [
        (
            a.get("detected_at"),
            a.get("anomaly_type"),
            a.get("metric_trigger"),
            a.get("description"),
            Json(a.get("event_ids"))
        )
        for a in anomalies
    ]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            execute_values(cur, sql, data)
            conn.commit()
            return len(anomalies)
