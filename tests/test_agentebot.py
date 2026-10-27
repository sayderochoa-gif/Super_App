"""Unit and integration tests for agentebot."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agentebot.database.connection import Base
from agentebot.database.models import Earthquake, Location, ImpactMetric
from agentebot.services.ingestion import IngestionService
from agentebot.agent.tools import (
    execute_safe_sql,
    get_seismic_statistics,
    query_earthquakes,
    get_tsunami_alerts,
)
from agentebot.agent.core import SeismicAgent


SAMPLE_GEOJSON_FEATURE = {
    "type": "Feature",
    "properties": {
        "mag": 4.5,
        "place": "35 km SW of Ovalle, Chile",
        "time": 1700000000000,
        "updated": 1700000100000,
        "tz": None,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000test",
        "detail": "detail_url",
        "felt": 12,
        "cdi": 4.1,
        "mmi": 4.8,
        "alert": "green",
        "status": "reviewed",
        "tsunami": 1,
        "sig": 312,
        "net": "us",
        "code": "7000test",
        "ids": ",us7000test,",
        "sources": ",us,",
        "types": ",origin,phase-data,",
        "nst": 45,
        "dmin": 0.32,
        "rms": 0.25,
        "gap": 85.0,
        "magType": "mww",
        "type": "earthquake",
        "title": "M 4.5 - 35 km SW of Ovalle, Chile",
    },
    "geometry": {
        "type": "Point",
        "coordinates": [-71.45, -30.85, 42.0],
    },
    "id": "us7000test",
}


@pytest.fixture
def test_session():
    """Create in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_feature_ingestion_and_normalization(test_session):
    """Test that a GeoJSON feature is correctly partitioned into the 3 relational tables."""
    service = IngestionService()
    feat_id, is_new = service.process_feature(SAMPLE_GEOJSON_FEATURE, test_session)
    test_session.commit()

    assert feat_id == "us7000test"
    assert is_new is True

    # 1. Location check
    loc = test_session.query(Location).first()
    assert loc is not None
    assert loc.place_name == "35 km SW of Ovalle, Chile"
    assert loc.country_or_state == "Chile"
    assert loc.latitude == -30.85
    assert loc.longitude == -71.45

    # 2. Earthquake check
    eq = test_session.query(Earthquake).filter(Earthquake.id == "us7000test").first()
    assert eq is not None
    assert eq.magnitude == 4.5
    assert eq.depth_km == 42.0
    assert eq.mag_type == "mww"
    assert eq.location_id == loc.id

    # 3. ImpactMetric check
    imp = test_session.query(ImpactMetric).filter(ImpactMetric.earthquake_id == "us7000test").first()
    assert imp is not None
    assert imp.felt == 12
    assert imp.tsunami == 1
    assert imp.sig == 312
    assert imp.alert == "green"


def test_upsert_idempotency(test_session):
    """Test that ingesting the same feature with updated values modifies existing records."""
    service = IngestionService()
    service.process_feature(SAMPLE_GEOJSON_FEATURE, test_session)
    test_session.commit()

    # Create modified payload (updated magnitude)
    updated_feature = dict(SAMPLE_GEOJSON_FEATURE)
    updated_feature["properties"] = dict(SAMPLE_GEOJSON_FEATURE["properties"])
    updated_feature["properties"]["mag"] = 4.8

    feat_id, is_new = service.process_feature(updated_feature, test_session)
    test_session.commit()

    assert feat_id == "us7000test"
    assert is_new is False

    eq = test_session.query(Earthquake).filter(Earthquake.id == "us7000test").first()
    assert eq.magnitude == 4.8
    assert test_session.query(Earthquake).count() == 1


def test_safe_sql_execution():
    """Verify safe SQL read execution and malicious/destructive query rejection."""
    # Permitted SELECT
    ok_res = execute_safe_sql("SELECT 1 as num")
    assert ok_res["status"] == "success"
    assert ok_res["data"][0]["num"] == 1

    # Forbidden DDL/DML
    del_res = execute_safe_sql("DELETE FROM earthquakes")
    assert del_res["status"] == "error"
    assert "Security policy violation" in del_res["message"]

    drop_res = execute_safe_sql("DROP TABLE locations")
    assert drop_res["status"] == "error"
    assert "Security policy violation" in drop_res["message"]


def test_agent_chat_reasoning():
    """Test conversational agent reasoning with stats and tsunami monitoring."""
    agent = SeismicAgent()
    
    # Help / Fallback
    res = agent.chat("Hola, ¿qué puedes hacer?")
    assert "SeismoAgent a tu disposición" in res

    # Stats query
    stats_res = agent.chat("Dame un resumen estadístico de la actividad sísmica")
    assert ("Reporte Estadístico" in stats_res) or ("vacía" in stats_res)

    # Tsunami query
    tsunami_res = agent.chat("¿Hay alertas de tsunami?")
    assert "Tsunami" in tsunami_res or "tsunami" in tsunami_res


def test_seismic_prevention_and_science_training():
    """Verify that the agent responds authoritatively to prevention and science questions cleanly without ***."""
    agent = SeismicAgent()

    test_cases = [
        ("¿Qué hacer durante un sismo?", ["Agacharse", "Cubrirse", "Sujetarse"]),
        ("¿Qué debe contener una mochila de emergencia?", ["72 horas", "Agua", "Botiquín"]),
        ("¿Qué es un sismo?", ["hipocentro", "epicentro", "energía"]),
        ("¿Se pueden predecir los sismos?", ["NINGÚN", "Alerta Temprana"]),
        ("¿Qué son las ondas P y S?", ["Ondas P", "Ondas S", "Cuerpo"]),
        ("¿Qué diferencia hay entre la escala Richter y Mercalli?", ["Magnitud", "Intensidad"]),
    ]

    for question, expected_keywords in test_cases:
        response = agent.chat(question)
        # Ensure strict cleanliness: NO triple asterisks
        assert "***" not in response, f"Found triple asterisks in response for '{question}'"
        # Ensure relevant knowledge keywords are present
        for kw in expected_keywords:
            assert kw.lower() in response.lower(), f"Expected keyword '{kw}' missing in response for '{question}'"


def test_admin_context_and_actions():
    """Verify that the agent answers questions about the Admin view, panels, and actions."""
    agent = SeismicAgent()

    admin_tests = [
        ("¿Qué veo en mi vista de administrador?", ["Telemetría", "Reportes IA", "Pipeline", "Cuarentena"]),
        ("¿Qué acciones puedo hacer como administrador?", ["Backfill", "Regenerar", "Cuarentena", "Airflow"]),
        ("¿Cómo hacer un backfill histórico?", ["Start Date", "End Date", "Min Magnitude", "Airflow"]),
        ("¿Por qué entran registros en la tabla de cuarentena?", ["Pandera", "Latitud", "cuarentena"]),
        ("¿Cuáles son las credenciales de Airflow?", ["8080", "airflow"]),
    ]

    for question, expected_keywords in admin_tests:
        response = agent.chat(question, user_role="admin")
        assert "***" not in response, f"Found triple asterisks in response for '{question}'"
        for kw in expected_keywords:
            assert kw.lower() in response.lower(), f"Expected keyword '{kw}' missing in response for '{question}'"


def test_batch_ingestion_savepoint_isolation(test_session):
    """Verify that a malformed feature in a batch does not abort subsequent valid features."""
    service = IngestionService()
    batch = [
        # 1. Invalid coordinates feature
        {
            "id": "broken_feat_1",
            "properties": {"mag": 3.0, "place": "Invalid Place"},
            "geometry": {"coordinates": [None, None]},
        },
        # 2. Valid feature
        SAMPLE_GEOJSON_FEATURE,
    ]

    res = service.ingest_features(batch, test_session)
    test_session.commit()

    assert res["total_features"] == 2
    assert res["inserted"] == 1
    assert res["errors_count"] == 1
    assert test_session.query(Earthquake).filter(Earthquake.id == "us7000test").count() == 1


def test_safe_sql_string_literal_and_chaining():
    """Verify safe SQL handles string literals without false positives and blocks chained statements."""
    # Query with 'drop' in a string literal - must SUCCEED
    ok_literal = execute_safe_sql("SELECT 'drop table test' as status_desc")
    assert ok_literal["status"] == "success"
    assert ok_literal["data"][0]["status_desc"] == "drop table test"

    # Query with multiple statements (chaining) - must FAIL
    chained_res = execute_safe_sql("SELECT 1; SELECT 2;")
    assert chained_res["status"] == "error"
    assert "Multiple statement execution" in chained_res["message"]


def test_resolved_database_url_memory():
    """Verify that in-memory sqlite URL is preserved verbatim."""
    from agentebot.config import Settings
    mem_settings = Settings(DATABASE_URL="sqlite:///:memory:")
    assert mem_settings.resolved_database_url == "sqlite:///:memory:"

