"""
Historical Backfill DAG for SismoWatch.
Allows manual or API-triggered parameterized backfills over historical time windows.
Queries USGS FDSNWS query endpoint, stages data, executes Quality Gate,
and promotes clean records to curated.earthquakes with guaranteed idempotency.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import requests

from airflow.decorators import dag, task
from airflow.models.param import Param

from quality_engine import flatten_geojson_features, evaluate_batch_quality
from db_utils import (
    insert_raw_feed,
    upsert_staging_earthquakes,
    upsert_curated_earthquakes,
    insert_quarantine_records,
    insert_quality_audit
)

logger = logging.getLogger("airflow.dag.backfill_historical")


def on_failure_alert(context: Dict[str, Any]):
    """Failure callback."""
    dag_id = context.get("dag", {}).dag_id if hasattr(context.get("dag"), "dag_id") else "dag_backfill_historical"
    task_id = context.get("task_instance").task_id if context.get("task_instance") else "unknown_task"
    exception = context.get("exception", "No exception info")
    logger.error(f"[BACKFILL PIPELINE ALERT] DAG '{dag_id}' Task '{task_id}' FAILED: {exception}")


DOC_MD = """
# Parametrized Historical Backfill DAG
- **Target Endpoint:** `https://earthquake.usgs.gov/fdsnws/event/1/query`
- **Configuration Parameters:**
  - `start_date`: Beginning date in `YYYY-MM-DD` format (Default: 30 days ago).
  - `end_date`: End date in `YYYY-MM-DD` format (Default: Today).
  - `min_mag`: Minimum magnitude filter (Default: 2.5).
- **Idempotency:** Utilizes Postgres `ON CONFLICT (id) DO UPDATE` to ensure safe re-execution without duplicate rows.
"""

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=45),
    "execution_timeout": timedelta(minutes=15),
    "on_failure_callback": on_failure_alert
}


@dag(
    dag_id="dag_backfill_historical",
    schedule=None,  # Manual or API trigger only
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=2,
    default_args=default_args,
    params={
        "start_date": Param(
            default=(datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
            type="string",
            description="Start date (YYYY-MM-DD)"
        ),
        "end_date": Param(
            default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            type="string",
            description="End date (YYYY-MM-DD)"
        ),
        "min_mag": Param(
            default=2.5,
            type="number",
            description="Minimum earthquake magnitude"
        )
    },
    tags=["sismowatch", "backfill", "historical", "usgs"],
    doc_md=DOC_MD
)
def backfill_historical_pipeline():

    @task(task_id="fetch_historical_from_usgs")
    def fetch_historical_from_usgs(**context) -> Dict[str, Any]:
        """
        Queries USGS FDSNWS service for the specified time range and magnitude.
        """
        conf = context.get("params") or {}
        start_date = conf.get("start_date") or (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = conf.get("end_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        min_mag = conf.get("min_mag", 2.5)

        base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
        params = {
            "format": "geojson",
            "starttime": start_date,
            "endtime": end_date,
            "minmagnitude": min_mag
        }

        logger.info(f"Querying USGS Historical backfill: {base_url} with params {params}")
        resp = requests.get(base_url, params=params, timeout=(10.0, 60.0))
        resp.raise_for_status()
        geojson_data = resp.json()

        features = geojson_data.get("features", [])
        logger.info(f"Retrieved {len(features)} historical features from USGS.")

        # Ingest raw payload
        raw_source_desc = f"{base_url}?starttime={start_date}&endtime={end_date}&minmagnitude={min_mag}"
        feed_id = insert_raw_feed(source=raw_source_desc, payload=geojson_data)

        return {
            "feed_id": feed_id,
            "feature_count": len(features),
            "start_date": start_date,
            "end_date": end_date,
            "min_mag": min_mag
        }

    @task(task_id="stage_and_curate_historical")
    def stage_and_curate_historical(meta: Dict[str, Any], **context) -> Dict[str, Any]:
        """
        Stages raw records, applies Pandera Quality Gate, quarantines invalid records,
        and executes idempotent UPSERT into curated.earthquakes.
        """
        feed_id = meta["feed_id"]
        dag_run_id = context.get("dag_run").run_id if context.get("dag_run") else "manual_backfill"

        # Re-fetch the saved feed payload
        from db_utils import get_db_connection
        sql = "SELECT payload FROM raw.earthquake_feeds WHERE id = %s;"
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (feed_id,))
                row = cur.fetchone()
                payload = row[0] if row else {}

        features = payload.get("features", [])
        flattened = flatten_geojson_features(features)

        # 1. Staging Upsert
        staged_count = upsert_staging_earthquakes(flattened)
        logger.info(f"Staged {staged_count} records from backfill.")

        # 2. Quality Gate Evaluation
        eval_result = evaluate_batch_quality(flattened, dag_run_id=dag_run_id)
        passed = eval_result["passed_records"]
        quarantine = eval_result["quarantine_records"]
        audit = eval_result["audit_summary"]

        # 3. Curated Upsert
        curated_count = upsert_curated_earthquakes(passed)

        # 4. Quarantine Insert
        quarantine_count = insert_quarantine_records(quarantine)

        # 5. Quality Audit Log
        insert_quality_audit(audit)

        logger.info(
            f"Backfill finished. Curated: {curated_count}, Quarantined: {quarantine_count}, "
            f"Quality Score: {audit['quality_score']}%"
        )
        return {
            "curated_count": curated_count,
            "quarantine_count": quarantine_count,
            "quality_score": audit["quality_score"]
        }

    hist_meta = fetch_historical_from_usgs()
    stage_and_curate_historical(hist_meta)


dag_instance = backfill_historical_pipeline()
