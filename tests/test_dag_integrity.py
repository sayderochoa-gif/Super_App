"""
Airflow DAG Integrity and Syntax Tests.
Verifies all DAG definition files in airflow/dags/ parse without syntax errors,
contain valid DAG objects, declare required tags, and have no cyclic task dependencies.
"""

import ast
import os
from pathlib import Path
import pytest

DAGS_FOLDER = Path(__file__).resolve().parent.parent / "airflow" / "dags"


def get_dag_files():
    """Discovers all Python DAG files in airflow/dags/."""
    files = list(DAGS_FOLDER.glob("dag_*.py"))
    assert len(files) >= 4, f"Expected at least 4 DAG files, found {len(files)}"
    return files


@pytest.mark.parametrize("dag_path", get_dag_files(), ids=lambda p: p.name)
def test_dag_syntax_and_ast_validity(dag_path: Path):
    """
    Validates Python syntax and compiles AST for each DAG file to prevent syntax errors.
    """
    with open(dag_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Compiling to AST validates syntax and grammar
    parsed = ast.parse(source_code, filename=str(dag_path))
    assert parsed is not None

    # Verify dag decorator or definition is present
    has_dag_definition = any(
        isinstance(node, ast.FunctionDef) and any(
            (isinstance(d, ast.Call) and getattr(d.func, "id", None) == "dag") or
            (isinstance(d, ast.Name) and d.id == "dag")
            for d in node.decorator_list
        )
        for node in ast.walk(parsed)
    )
    assert has_dag_definition, f"{dag_path.name} must declare a @dag decorated pipeline."


def test_dagbag_import_and_no_cycles():
    """
    If apache-airflow is installed, imports DAGs through Airflow DagBag
    and verifies no import errors and no cyclic dependencies.
    """
    try:
        from airflow.models import DagBag
        dagbag = DagBag(dag_folder=str(DAGS_FOLDER), include_examples=False)

        assert len(dagbag.import_errors) == 0, f"Airflow DAG import errors: {dagbag.import_errors}"
        assert len(dagbag.dags) >= 4, f"Expected 4 DAGs, loaded: {list(dagbag.dags.keys())}"

        # Verify cycle detection and tags for each DAG
        expected_dags = [
            "dag_ingestion_realtime",
            "dag_transformation_quality",
            "dag_ai_daily_report",
            "dag_backfill_historical"
        ]
        for dag_id in expected_dags:
            assert dag_id in dagbag.dags, f"DAG '{dag_id}' not found in DagBag"
            dag = dagbag.dags[dag_id]
            # Cycle detection
            dag.test_cycle()
            # Must have tags
            assert dag.tags is not None and len(dag.tags) > 0, f"DAG {dag_id} missing tags"
            # Must have doc_md
            assert dag.doc_md is not None, f"DAG {dag_id} missing doc_md"
    except ImportError:
        # Airflow core not installed in local environment; AST tests verify file integrity
        pytest.skip("apache-airflow is not installed in the test environment (runs inside Airflow container).")
