"""
Transformation and Quality Gate DAG for SismoWatch.
Extracts the latest raw USGS GeoJSON, flattens into staging.earthquakes (idempotent UPSERT),
applies Pandera Quality Gate, quarantines invalid records with root-cause attribution,
promotes validated records to curated.earthquakes, and logs quality metrics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from airflow.decorators import dag, task, task_group

from quality_engine import flatten_geojson_features, evaluate_batch_quality, check_feed_freshness
from db_utils import (
    get_latest_raw_feed,
    upsert_staging_earthquakes,
    upsert_curated_earthquakes,
    insert_quarantine_records,
    insert_quality_audit
)

logger = logging.getLogger("airflow.dag.transformation_quality")


def on_failure_alert(context: Dict[str, Any]):
    """Failure callback logging error details."""
    dag_id = context.get("dag", {}).dag_id if hasattr(context.get("dag"), "dag_id") else "dag_transformation_quality"
    task_id = context.get("task_instance").task_id if context.get("task_instance") else "unknown_task"
    exception = context.get("exception", "No exception info")
    logger.error(f"[QUALITY PIPELINE ALERT] DAG '{dag_id}' Task '{task_id}' FAILED: {exception}")


DOC_MD = """
# Transformation & Data Quality DAG: SismoWatch
- **Role:** Extracts from `raw.earthquake_feeds`, normalizes into `staging`, and executes Pandera Quality Gate.
- **Routing:**
  - Valid records -> UPSERT into `curated.earthquakes`.
  - Violations -> Quarantined into `curated.quarantine` with specific failure reasons.
- **Audit:** Records metrics, rule adherence, and quality score in `curated.quality_audit`.
"""

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(seconds=20),
    "execution_timeout": timedelta(minutes=5),
    "on_failure_callback": on_failure_alert
}


@dag(
    dag_id="dag_transformation_quality",
    schedule=None,  # Triggered by dag_ingestion_realtime or manually
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["sismowatch", "transformation", "quality_gate", "curated"],
    doc_md=DOC_MD
)
def transformation_quality_pipeline():

    @task(task_id="extract_raw_and_stage")
    def extract_raw_and_stage(**context) -> Dict[str, Any]:
        """
        Retrieves the latest raw feed from raw.earthquake_feeds,
        flattens features and loads them into staging.earthquakes via UPSERT.
        """
        raw_feed = get_latest_raw_feed()
        if not raw_feed:
            logger.warning("No raw feed available in raw.earthquake_feeds.")
            return {"raw_id": None, "features_count": 0, "staging_count": 0}

        raw_id = raw_feed["id"]
        payload = raw_feed["payload"]
        features = payload.get("features", [])

        flattened = flatten_geojson_features(features)
        staged_count = upsert_staging_earthquakes(flattened)
        logger.info(f"Loaded {staged_count} records into staging.earthquakes from raw feed #{raw_id}")

        return {
            "raw_id": raw_id,
            "features_count": len(features),
            "staged_count": staged_count
        }

    @task_group(group_id="quality_and_curation_gate")
    def quality_and_curation_group(stage_meta: Dict[str, Any]):

        @task(task_id="evaluate_and_route_records")
        def evaluate_and_route_records(**context) -> Dict[str, Any]:
            """
            Applies the Pandera Quality Gate:
            - Validates bounds for coordinates, magnitude, depth, and time.
            - Inserts quarantined records with detailed failure descriptions.
            - Upserts approved records into curated.earthquakes.
            - Writes run score into curated.quality_audit.
            """
            raw_feed = get_latest_raw_feed()
            if not raw_feed or not raw_feed.get("payload"):
                logger.info("No payload found to evaluate quality.")
                return {"passed": 0, "quarantined": 0, "quality_score": 100.0}

            features = raw_feed["payload"].get("features", [])
            flattened = flatten_geojson_features(features)
            
            dag_run_id = context.get("dag_run").run_id if context.get("dag_run") else "manual_run"
            eval_result = evaluate_batch_quality(flattened, dag_run_id=dag_run_id)

            passed_records = eval_result["passed_records"]
            quarantine_records = eval_result["quarantine_records"]
            audit_summary = eval_result["audit_summary"]

            # 1. Route passed records to Curated layer
            promoted_count = upsert_curated_earthquakes(passed_records)
            logger.info(f"Promoted {promoted_count} valid records to curated.earthquakes.")

            # 2. Route invalid records to Quarantine table
            quarantined_count = insert_quarantine_records(quarantine_records)
            if quarantined_count > 0:
                logger.warning(f"Quarantined {quarantined_count} records failing Quality Gate rules.")

            # 3. Log quality metrics to quality_audit
            audit_id = insert_quality_audit(audit_summary)
            logger.info(
                f"Quality Audit #{audit_id} logged. Score: {audit_summary['quality_score']}% "
                f"({len(passed_records)} passed, {len(quarantine_records)} rejected)."
            )

            # 4. Freshness evaluation
            if passed_records:
                latest_time = max(r["time"] for r in passed_records if r.get("time"))
                freshness = check_feed_freshness(latest_time, threshold_hours=6.0)
                if not freshness["fresh"]:
                    logger.warning(freshness["warning"])

            return {
                "passed": promoted_count,
                "quarantined": quarantined_count,
                "quality_score": audit_summary["quality_score"]
            }

        evaluate_and_route_records()

    stage_result = extract_raw_and_stage()
    quality_and_curation_group(stage_result)


dag_instance = transformation_quality_pipeline()
