"""
Transformation and GeoJSON Parsing Tests.
Validates flattening of USGS GeoJSON features into the staging schema structure.
"""

from datetime import datetime, timezone
import pytest
from quality_engine import flatten_geojson_features, parse_epoch_ms


def test_parse_epoch_ms_valid():
    epoch_ms = 1729828472910
    dt = parse_epoch_ms(epoch_ms)
    assert isinstance(dt, datetime)
    assert dt.tzinfo is not None
    assert dt.year == 2024


def test_parse_epoch_ms_none_or_invalid():
    assert parse_epoch_ms(None) is None
    assert parse_epoch_ms("invalid_date_string") is None


def test_flatten_geojson_features_extraction(sample_usgs_geojson):
    features = sample_usgs_geojson["features"]
    flattened = flatten_geojson_features(features)

    assert len(flattened) == 2

    first = flattened[0]
    assert first["id"] == "pr74291826"
    assert first["mag"] == 3.4
    assert first["place"] == "12 km SW of Guánica, Puerto Rico"
    assert first["longitude"] == -66.98
    assert first["latitude"] == 17.89
    assert first["depth_km"] == 12.5
    assert first["tsunami"] == 0
    assert isinstance(first["time"], datetime)

    second = flattened[1]
    assert second["id"] == "us6000test"
    assert second["mag"] == 6.8
    assert second["tsunami"] == 1
    assert second["longitude"] == 169.5
    assert second["latitude"] == -21.8
    assert second["depth_km"] == 10.0


def test_flatten_empty_features():
    flattened = flatten_geojson_features([])
    assert flattened == []


def test_flatten_handles_missing_fields_gracefully():
    malformed_features = [
        {
            "id": "missing_coords",
            "properties": {"mag": 4.1, "time": 1729828472910},
            "geometry": {}
        }
    ]
    flattened = flatten_geojson_features(malformed_features)
    assert len(flattened) == 1
    assert flattened[0]["id"] == "missing_coords"
    assert flattened[0]["longitude"] is None
    assert flattened[0]["latitude"] is None
    assert flattened[0]["depth_km"] is None
