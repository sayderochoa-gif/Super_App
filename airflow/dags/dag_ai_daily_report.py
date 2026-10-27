"""
Daily AI Executive Report and Anomaly Detection DAG for SismoWatch.
Executes daily at 00:05 UTC.
- Calculates exact deterministic KPIs over the previous 24-hour window.
- Runs IsolationForest and spatial clustering anomaly detection.
- Generates an executive narrative report via LLM (with deterministic template fallback).
- Enforces strict post-generation factual consistency check.
- Persists outputs into curated.ai_daily_reports and curated.ai_anomalies.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import pandas as pd

from airflow.decorators import dag, task, task_group

from ai_engine import (
    calculate_deterministic_kpis,
    detect_seismic_anomalies,
    generate_ai_report
)
from db_utils import (
    get_db_connection,
    upsert_ai_daily_report,
    insert_ai_anomalies
)

logger = logging.getLogger("airflow.dag.ai_daily_report")


def on_failure_alert(context: Dict[str, Any]):
    """Failure notification callback."""
    dag_id = context.get("dag", {}).dag_id if hasattr(context.get("dag"), "dag_id") else "dag_ai_daily_report"
    task_id = context.get("task_instance").task_id if context.get("task_instance") else "unknown_task"
    exception = context.get("exception", "No exception info")
    logger.error(f"[AI REPORT PIPELINE ALERT] DAG '{dag_id}' Task '{task_id}' FAILED: {exception}")


DOC_MD = """
# Daily AI Executive Report & Anomaly Detection DAG
- **Schedule:** `@daily` (00:05 UTC)
- **Layer:** `curated`
- **Methodology:**
  1. **Deterministic Calculation:** Computes KPIs from verified `curated.earthquakes` (24h window).
  2. **Anomaly Engine:** IsolationForest & statistical spatial clustering for seismic swarm detection.
  3. **Grounded Reporting:** Synthesizes narrative via LLM with strict factual validation and deterministic template fallback.
"""

default_args = {
    "owner": "data_engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=10),
    "on_failure_callback": on_failure_alert
}


@dag(
    dag_id="dag_ai_daily_report",
    schedule="5 0 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["sismowatch", "ai", "reports", "anomalies", "analytics"],
    doc_md=DOC_MD
)
def ai_daily_report_pipeline():

    @task(task_id="compute_deterministic_kpis")
    def compute_deterministic_kpis(**context) -> Dict[str, Any]:
        """
        Queries curated.earthquakes for events in the last 24 hours
        and computes deterministic summary statistics.
        """
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
        report_date = yesterday.strftime("%Y-%m-%d")

        sql = """
            SELECT id, mag, place, time, tsunami, depth_km, latitude, longitude
            FROM curated.earthquakes
            WHERE time >= %s AND time <= %s;
        """
        with get_db_connection() as conn:
            df = pd.read_sql(sql, conn, params=(yesterday, now))

        kpis = calculate_deterministic_kpis(df)
        logger.info(
            f"Computed deterministic KPIs for {report_date}: "
            f"Total={kpis['total_events']}, MaxMag={kpis['max_magnitude']}, "
            f"AvgMag={kpis['avg_magnitude']}, Tsunamis={kpis['tsunami_alerts']}"
        )
        return {
            "report_date": report_date,
            "kpis": kpis,
            "window_start": yesterday.isoformat(),
            "window_end": now.isoformat()
        }

    @task(task_id="detect_anomalies_task")
    def detect_anomalies_task(kpi_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detects unusual seismic events or spatial swarm concentrations.
        """
        window_start = kpi_context["window_start"]
        window_end = kpi_context["window_end"]

        sql = """
            SELECT id, mag, place, time, tsunami, depth_km, latitude, longitude
            FROM curated.earthquakes
            WHERE time >= %s AND time <= %s;
        """
        with get_db_connection() as conn:
            df = pd.read_sql(sql, conn, params=(window_start, window_end))

        anomalies = detect_seismic_anomalies(df)
        inserted_count = insert_ai_anomalies(anomalies)
        logger.info(f"Anomaly detection complete. Identified and recorded {inserted_count} anomalies.")
        return anomalies

    @task(task_id="synthesize_and_persist_report")
    def synthesize_and_persist_report(kpi_context: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates and verifies the daily narrative report, saving it to curated.ai_daily_reports.
        """
        report_date = kpi_context["report_date"]
        kpis = kpi_context["kpis"]

        report_payload = generate_ai_report(
            report_date=report_date,
            kpis=kpis,
            anomalies=anomalies
        )
        report_payload["report_date"] = report_date

        report_id = upsert_ai_daily_report(report_payload)
        logger.info(
            f"AI Report #{report_id} successfully stored for {report_date} "
            f"(Model: {report_payload['model_name']}, Latency: {report_payload['latency_sec']}s, "
            f"Tokens: {report_payload['tokens_used']})"
        )
        return {"report_id": report_id, "report_date": report_date}

    kpi_res = compute_deterministic_kpis()
    anomalies_res = detect_anomalies_task(kpi_res)
    synthesize_and_persist_report(kpi_res, anomalies_res)


dag_instance = ai_daily_report_pipeline()
