"""
Real-time Earthquake Ingestion DAG for SismoWatch.
Polls USGS hourly GeoJSON feed every 5 minutes, validates network connectivity,
persists raw payload with idempotency into raw.earthquake_feeds,
and triggers the downstream transformation and quality gate DAG.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
import requests

from quality_engine import check_feed_freshness
from db_utils import insert_raw_feed

logger = logging.getLogger("airflow.dag.ingestion_realtime")

USGS_REALTIME_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"


def on_failure_alert(context: Dict[str, Any]):
    """Failure callback logging error details and context."""
    dag_id = context.get("dag", {}).dag_id if hasattr(context.get("dag"), "dag_id") else "dag_ingestion_realtime"
    task_id = context.get("task_instance").task_id if context.get("task_instance") else "unknown_task"
    exception = context.get("exception", "No exception info provided")
    logger.error(
        f"[PIPELINE ALERT] DAG '{dag_id}' Task '{task_id}' FAILED. "
        f"Execution Time: {datetime.now(timezone.utc).isoformat()}. Reason: {exception}"
    )


DOC_MD = """
# Real-Time Ingestion DAG: SismoWatch
- **Source:** USGS Earthquake API (`all_hour.geojson`)
- **Frequency:** `*/5 * * * *` (Every 5 minutes)
- **Retry Strategy:** 3 retries, exponential backoff (30s initial), 2m execution timeout.
- **Storage Target:** `raw.earthquake_feeds`
- **Downstream:** Triggers `dag_transformation_quality` on successful ingestion.
"""

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(seconds=30),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=2),
    "on_failure_callback": on_failure_alert
}


@dag(
    dag_id="dag_ingestion_realtime",
    schedule="*/5 * * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["sismowatch", "ingestion", "realtime", "usgs"],
    doc_md=DOC_MD
)
def ingestion_realtime_pipeline():

    @task(task_id="fetch_and_store_usgs_feed")
    def fetch_and_store_usgs_feed() -> Dict[str, Any]:
        """
        Fetches the GeoJSON feed from USGS with timeout handling
        and stores the raw payload into the raw data layer.
        """
        logger.info(f"Initiating request to USGS feed: {USGS_REALTIME_URL}")
        try:
            response = requests.get(
                USGS_REALTIME_URL,
                timeout=(5.0, 30.0),
                headers={"User-Agent": "SismoWatch-DataPlatform/1.0"}
            )
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Network error while connecting to USGS: {exc}")
            # Re-raise so Airflow triggers configured retries
            raise

        features = payload.get("features", [])
        feature_count = len(features)
        logger.info(f"Successfully retrieved USGS GeoJSON containing {feature_count} features.")

        # Persist raw payload
        feed_id = insert_raw_feed(source=USGS_REALTIME_URL, payload=payload)
        logger.info(f"Persisted raw feed to raw.earthquake_feeds with ID: {feed_id}")

        return {
            "feed_id": feed_id,
            "feature_count": feature_count,
            "ingested_at": datetime.now(timezone.utc).isoformat()
        }

    trigger_transformation = TriggerDagRunOperator(
        task_id="trigger_transformation_quality",
        trigger_dag_id="dag_transformation_quality",
        wait_for_completion=False,
        reset_dag_run=True
    )

    feed_meta = fetch_and_store_usgs_feed()
    feed_meta >> trigger_transformation


dag_instance = ingestion_realtime_pipeline()
