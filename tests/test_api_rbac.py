"""
API Authentication & Role-Based Access Control (RBAC) Tests.
Validates:
1. Anonymous/Unauthenticated requests return HTTP 401 Unauthorized.
2. Viewer role cannot access quarantine or admin endpoints (HTTP 403 Forbidden).
3. Admin role has unrestricted access to admin and quarantine endpoints (HTTP 200 OK).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.models.user import User
from app.security import get_current_user
from app.database import get_db

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. ANONYMOUS USERS (HTTP 401 UNAUTHORIZED)
# -----------------------------------------------------------------------------
def test_unauthenticated_kpis_returns_401():
    response = client.get("/api/kpis")
    assert response.status_code == 401


def test_unauthenticated_events_returns_401():
    response = client.get("/api/events")
    assert response.status_code == 401


def test_unauthenticated_quarantine_returns_401():
    response = client.get("/api/quality/quarantine")
    assert response.status_code == 401


def test_unauthenticated_admin_backfill_returns_401():
    response = client.post("/api/admin/backfill", json={
        "start_date": "2025-01-01",
        "end_date": "2025-01-30",
        "min_mag": 2.5
    })
    assert response.status_code == 401


# -----------------------------------------------------------------------------
# 2. VIEWER ROLE (HTTP 403 FORBIDDEN ON ADMIN/QUARANTINE, 200 ON ALLOWED)
# -----------------------------------------------------------------------------
def test_viewer_cannot_access_quarantine(mock_viewer_user):
    """Viewers must be rejected with 403 Forbidden when requesting quarantine table."""
    app.dependency_overrides[get_current_user] = lambda: mock_viewer_user

    try:
        response = client.get("/api/quality/quarantine")
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_viewer_cannot_trigger_backfill(mock_viewer_user):
    """Viewers cannot trigger backfill DAG."""
    app.dependency_overrides[get_current_user] = lambda: mock_viewer_user

    try:
        response = client.post("/api/admin/backfill", json={
            "start_date": "2025-01-01",
            "end_date": "2025-01-30",
            "min_mag": 2.5
        })
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_viewer_cannot_regenerate_reports(mock_viewer_user):
    """Viewers cannot force AI report regeneration."""
    app.dependency_overrides[get_current_user] = lambda: mock_viewer_user

    try:
        response = client.post("/api/admin/reports/regenerate")
        assert response.status_code == 403
        assert "Access forbidden" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 3. ADMIN ROLE (HTTP 200 OK ON QUARANTINE & ADMIN ACTIONS)
# -----------------------------------------------------------------------------
def test_admin_can_access_quarantine(mock_admin_user):
    """Admins can view quarantine details."""
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    from unittest.mock import MagicMock
    mock_db = AsyncMock()
    mock_res_count = MagicMock()
    mock_res_count.scalar_one.return_value = 0
    mock_res_data = MagicMock()
    mock_res_data.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [mock_res_count, mock_res_data]
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/quality/quarantine")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    finally:
        app.dependency_overrides.clear()


@patch("app.routers.admin.trigger_airflow_dag")
def test_admin_can_trigger_backfill(mock_trigger, mock_admin_user):
    """Admins can trigger historical backfill."""
    mock_trigger.return_value = {"status": "success", "data": {"dag_run_id": "test_backfill_1"}}
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    try:
        response = client.post("/api/admin/backfill", json={
            "start_date": "2025-01-01",
            "end_date": "2025-01-10",
            "min_mag": 3.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Historical backfill triggered" in data["message"]
    finally:
        app.dependency_overrides.clear()


@patch("app.routers.admin.trigger_airflow_dag")
def test_admin_can_regenerate_reports(mock_trigger, mock_admin_user):
    """Admins can trigger AI daily report regeneration."""
    mock_trigger.return_value = {"status": "success", "data": {"dag_run_id": "test_ai_report_1"}}
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    try:
        response = client.post("/api/admin/reports/regenerate")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "AI daily report regeneration task triggered" in data["message"]
    finally:
        app.dependency_overrides.clear()
