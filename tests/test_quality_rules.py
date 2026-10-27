"""
Quality Gate and Quarantine Validation Tests.
Verifies Pandera / rule-based validation logic, score attribution,
and specific quarantine rejection reasons.
"""

from datetime import datetime, timezone, timedelta
import pytest
from quality_engine import validate_single_record, evaluate_batch_quality, check_feed_freshness


def test_valid_record_passes_quality_gate():
    now = datetime.now(timezone.utc)
    valid_record = {
        "id": "us7000test1",
        "mag": 4.5,
        "latitude": 34.05,
        "longitude": -118.25,
        "depth_km": 10.2,
        "time": now - timedelta(minutes=15),
        "place": "Los Angeles, CA",
        "tsunami": 0
    }
    is_valid, reasons = validate_single_record(valid_record)
    assert is_valid is True
    assert len(reasons) == 0


def test_out_of_bounds_latitude_quarantined():
    now = datetime.now(timezone.utc)
    invalid_record = {
        "id": "err_lat",
        "mag": 3.0,
        "latitude": 150.0,  # Invalid: bounds [-90, 90]
        "longitude": -70.0,
        "depth_km": 5.0,
        "time": now
    }
    is_valid, reasons = validate_single_record(invalid_record)
    assert is_valid is False
    assert any("Latitude 150.0 outside valid bounds" in r for r in reasons)


def test_extreme_magnitude_quarantined():
    now = datetime.now(timezone.utc)
    invalid_record = {
        "id": "err_mag",
        "mag": 15.0,  # Physically implausible magnitude
        "latitude": 10.0,
        "longitude": 20.0,
        "depth_km": 8.0,
        "time": now
    }
    is_valid, reasons = validate_single_record(invalid_record)
    assert is_valid is False
    assert any("Magnitude 15.0 outside plausible range" in r for r in reasons)


def test_future_timestamp_quarantined():
    future_time = datetime.now(timezone.utc) + timedelta(hours=2)
    invalid_record = {
        "id": "err_time",
        "mag": 2.5,
        "latitude": 0.0,
        "longitude": 0.0,
        "depth_km": 15.0,
        "time": future_time
    }
    is_valid, reasons = validate_single_record(invalid_record)
    assert is_valid is False
    assert any("Event time is in future" in r for r in reasons)


def test_missing_or_empty_id_quarantined():
    now = datetime.now(timezone.utc)
    invalid_record = {
        "id": "   ",
        "mag": 2.5,
        "latitude": 0.0,
        "longitude": 0.0,
        "depth_km": 15.0,
        "time": now
    }
    is_valid, reasons = validate_single_record(invalid_record)
    assert is_valid is False
    assert any("Invalid or missing 'id'" in r for r in reasons)


def test_evaluate_batch_quality_routing_and_score():
    now = datetime.now(timezone.utc)
    batch = [
        # Valid
        {
            "id": "rec_ok_1",
            "mag": 2.1,
            "latitude": 19.4,
            "longitude": -155.2,
            "depth_km": 4.0,
            "time": now - timedelta(minutes=5)
        },
        # Valid
        {
            "id": "rec_ok_2",
            "mag": 5.4,
            "latitude": -33.4,
            "longitude": -70.6,
            "depth_km": 35.0,
            "time": now - timedelta(minutes=10)
        },
        # Invalid (mag = 12.0)
        {
            "id": "rec_bad_1",
            "mag": 12.0,
            "latitude": 40.0,
            "longitude": 15.0,
            "depth_km": 10.0,
            "time": now - timedelta(minutes=2)
        },
        # Invalid (lon = -250.0)
        {
            "id": "rec_bad_2",
            "mag": 3.0,
            "latitude": 10.0,
            "longitude": -250.0,
            "depth_km": 10.0,
            "time": now - timedelta(minutes=2)
        }
    ]

    res = evaluate_batch_quality(batch, dag_run_id="test_run_1")

    assert len(res["passed_records"]) == 2
    assert len(res["quarantine_records"]) == 2
    assert res["audit_summary"]["total_records"] == 4
    assert res["audit_summary"]["passed_records"] == 2
    assert res["audit_summary"]["rejected_records"] == 2
    assert res["audit_summary"]["quality_score"] == 50.0

    # Ensure quarantine records have rejection reasons
    reasons = [q["reason"] for q in res["quarantine_records"]]
    assert any("Magnitude 12.0 outside plausible range" in r for r in reasons)
    assert any("Longitude -250.0 outside valid bounds" in r for r in reasons)


def test_check_feed_freshness():
    now = datetime.now(timezone.utc)
    fresh_time = now - timedelta(minutes=30)
    stale_time = now - timedelta(hours=12)

    fresh_res = check_feed_freshness(fresh_time, threshold_hours=6.0)
    assert fresh_res["fresh"] is True
    assert fresh_res["warning"] is None

    stale_res = check_feed_freshness(stale_time, threshold_hours=6.0)
    assert stale_res["fresh"] is False
    assert "Feed freshness alert" in stale_res["warning"]
