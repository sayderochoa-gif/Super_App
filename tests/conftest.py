"""
Pytest Configuration and Shared Test Fixtures for SismoWatch.
"""

import sys
import os
from pathlib import Path
import pytest
from datetime import datetime, timezone, timedelta

# Ensure project root, airflow/plugins, airflow/dags, and backend are on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "airflow" / "plugins"))
sys.path.insert(0, str(PROJECT_ROOT / "airflow" / "dags"))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Set test environment variables
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-unit-testing-32-chars-long"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["ADMIN_USER"] = "admin@sismowatch.com"
os.environ["ADMIN_PASSWORD"] = "AdminTest123!"
os.environ["VIEWER_USER"] = "viewer@sismowatch.com"
os.environ["VIEWER_PASSWORD"] = "ViewerTest123!"

from jose import jwt
from app.config import settings
from app.models.user import User
from app.security import get_password_hash


@pytest.fixture
def sample_usgs_geojson():
    """Returns a realistic USGS GeoJSON payload sample."""
    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": 1729829391020,
            "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
            "title": "USGS All Earthquakes, Past Hour",
            "status": 200,
            "api": "1.10.3",
            "count": 2
        },
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "mag": 3.4,
                    "place": "12 km SW of Guánica, Puerto Rico",
                    "time": 1729828472910,
                    "updated": 1729829391020,
                    "tz": None,
                    "url": "https://earthquake.usgs.gov/earthquakes/event/pr74291826",
                    "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/pr74291826.geojson",
                    "felt": 5,
                    "cdi": 3.4,
                    "mmi": 3.8,
                    "alert": "green",
                    "status": "reviewed",
                    "tsunami": 0,
                    "sig": 178,
                    "net": "pr",
                    "code": "74291826",
                    "ids": ",pr74291826,",
                    "sources": ",pr,",
                    "types": ",origin,phase-data,",
                    "nst": 18,
                    "dmin": 0.08,
                    "rms": 0.24,
                    "gap": 82,
                    "magType": "md",
                    "type": "earthquake",
                    "title": "M 3.4 - 12 km SW of Guánica, Puerto Rico"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [-66.98, 17.89, 12.5]
                },
                "id": "pr74291826"
            },
            {
                "type": "Feature",
                "properties": {
                    "mag": 6.8,
                    "place": "150 km ESE of Tadine, New Caledonia",
                    "time": 1729827000000,
                    "updated": 1729828000000,
                    "tz": None,
                    "url": "https://earthquake.usgs.gov/earthquakes/event/us6000test",
                    "detail": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/us6000test.geojson",
                    "felt": 120,
                    "cdi": 6.1,
                    "mmi": 6.5,
                    "alert": "yellow",
                    "status": "reviewed",
                    "tsunami": 1,
                    "sig": 710,
                    "net": "us",
                    "code": "6000test",
                    "ids": ",us6000test,",
                    "sources": ",us,",
                    "types": ",origin,phase-data,",
                    "nst": 65,
                    "dmin": 1.2,
                    "rms": 0.8,
                    "gap": 32,
                    "magType": "mww",
                    "type": "earthquake",
                    "title": "M 6.8 - 150 km ESE of Tadine, New Caledonia"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [169.5, -21.8, 10.0]
                },
                "id": "us6000test"
            }
        ]
    }


@pytest.fixture
def admin_token():
    """Generates a valid JWT token for an admin user."""
    payload = {
        "sub": "admin@sismowatch.com",
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def viewer_token():
    """Generates a valid JWT token for a viewer user."""
    payload = {
        "sub": "viewer@sismowatch.com",
        "role": "viewer",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def mock_admin_user():
    return User(
        id=1,
        username="admin@sismowatch.com",
        hashed_password=get_password_hash("AdminTest123!"),
        role="admin",
        is_active=True
    )


@pytest.fixture
def mock_viewer_user():
    return User(
        id=2,
        username="viewer@sismowatch.com",
        hashed_password=get_password_hash("ViewerTest123!"),
        role="viewer",
        is_active=True
    )
