"""Data ingestion service: parses GeoJSON feeds and performs relational upserts."""

from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from agentebot.database.connection import get_db, init_db
from agentebot.database.models import Earthquake, Location, ImpactMetric
from agentebot.services.usgs_client import usgs_client

logger = logging.getLogger(__name__)


def parse_timestamp(ms: Optional[int]) -> Optional[datetime]:
    """Convert millisecond epoch timestamp to UTC datetime."""
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def extract_region_from_place(place: Optional[str]) -> str:
    """
    Extract country or state descriptor from USGS 'place' string.
    Example: '10 km NE of Pahala, Hawaii' -> 'Hawaii'
             'Northern California' -> 'Northern California'
             'Vanuatu' -> 'Vanuatu'
    """
    if not place:
        return "Unknown"

    # Common pattern: "XX km [DIR] of City, State/Country"
    if "," in place:
        parts = place.split(",")
        return parts[-1].strip()

    # Pattern: "Region region"
    clean = re.sub(r"^\d+\s*km\s+[NESWnesw]+\s+of\s+", "", place, flags=re.IGNORECASE)
    return clean.strip() or "Unknown"


class IngestionService:
    """Coordinates parsing, normalization, and relational upsert of seismic data."""

    def process_feature(
        self, feature: Dict[str, Any], session: Session
    ) -> Tuple[str, bool]:
        """
        Normalize and upsert a single GeoJSON earthquake feature into the 3 relational tables.

        Returns:
            Tuple of (earthquake_id, is_new_record)
        """
        feat_id = feature.get("id")
        if not feat_id:
            raise ValueError("Feature is missing required 'id' attribute.")

        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []

        if len(coordinates) < 2 or coordinates[0] is None or coordinates[1] is None:
            raise ValueError(f"Feature {feat_id} has invalid coordinates: {coordinates}")

        try:
            longitude = round(float(coordinates[0]), 6)
            latitude = round(float(coordinates[1]), 6)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Feature {feat_id} has non-numeric coordinates: {coordinates} ({e})")

        depth_km = None
        if len(coordinates) > 2 and coordinates[2] is not None:
            try:
                depth_km = round(float(coordinates[2]), 4)
            except (ValueError, TypeError):
                depth_km = None

        # 1. Location Normalization
        place_name = properties.get("place") or f"Coords ({latitude:.2f}, {longitude:.2f})"
        region = extract_region_from_place(place_name)

        # Look up or create location
        location = (
            session.query(Location)
            .filter(
                Location.latitude == latitude,
                Location.longitude == longitude,
                Location.place_name == place_name,
            )
            .first()
        )

        if not location:
            location = Location(
                place_name=place_name,
                country_or_state=region,
                latitude=latitude,
                longitude=longitude,
            )
            session.add(location)
            session.flush()  # Generate location.id

        # 2. Earthquake Entity Upsert
        eq_time = parse_timestamp(properties.get("time")) or datetime.now(timezone.utc)
        eq_updated = parse_timestamp(properties.get("updated"))
        mag = properties.get("mag")
        mag_val = float(mag) if mag is not None else None

        earthquake = session.query(Earthquake).filter(Earthquake.id == feat_id).first()
        is_new = earthquake is None

        if is_new:
            earthquake = Earthquake(
                id=feat_id,
                location_id=location.id,
                magnitude=mag_val,
                mag_type=properties.get("magType"),
                time=eq_time,
                updated=eq_updated,
                depth_km=depth_km,
                event_type=properties.get("type") or "earthquake",
                title=properties.get("title"),
                url=properties.get("url"),
            )
            session.add(earthquake)
            session.flush()
        else:
            earthquake.location_id = location.id
            earthquake.magnitude = mag_val
            earthquake.mag_type = properties.get("magType")
            earthquake.updated = eq_updated
            earthquake.depth_km = depth_km
            earthquake.event_type = properties.get("type") or earthquake.event_type
            earthquake.title = properties.get("title")
            earthquake.url = properties.get("url")

        # 3. Impact Metrics Upsert
        tsunami_raw = properties.get("tsunami")
        try:
            tsunami_val = int(tsunami_raw) if tsunami_raw is not None else 0
        except (ValueError, TypeError):
            tsunami_val = 0

        nst_raw = properties.get("nst")
        try:
            nst_val = int(nst_raw) if nst_raw is not None else None
        except (ValueError, TypeError):
            nst_val = None

        sig_raw = properties.get("sig")
        try:
            sig_val = int(sig_raw) if sig_raw is not None else None
        except (ValueError, TypeError):
            sig_val = None

        impact = session.query(ImpactMetric).filter(ImpactMetric.earthquake_id == feat_id).first()
        if not impact:
            impact = ImpactMetric(
                earthquake_id=feat_id,
                felt=properties.get("felt"),
                cdi=properties.get("cdi"),
                mmi=properties.get("mmi"),
                alert=properties.get("alert"),
                tsunami=tsunami_val,
                sig=sig_val,
                status=properties.get("status") or "automatic",
                nst=nst_val,
                dmin=properties.get("dmin"),
                rms=properties.get("rms"),
                gap=properties.get("gap"),
                net=properties.get("net"),
                code=str(properties.get("code") or ""),
            )
            session.add(impact)
        else:
            impact.felt = properties.get("felt")
            impact.cdi = properties.get("cdi")
            impact.mmi = properties.get("mmi")
            impact.alert = properties.get("alert")
            impact.tsunami = tsunami_val
            impact.sig = sig_val
            impact.status = properties.get("status") or impact.status
            impact.nst = nst_val
            impact.dmin = properties.get("dmin")
            impact.rms = properties.get("rms")
            impact.gap = properties.get("gap")
            impact.net = properties.get("net")
            impact.code = str(properties.get("code") or "")

        return feat_id, is_new

    def ingest_features(
        self, features: List[Dict[str, Any]], session: Session
    ) -> Dict[str, Any]:
        """Ingest a list of GeoJSON features in a single transaction with savepoint isolation."""
        inserted = 0
        updated = 0
        errors: List[str] = []

        for feature in features:
            try:
                with session.begin_nested():
                    _, is_new = self.process_feature(feature, session)
                    if is_new:
                        inserted += 1
                    else:
                        updated += 1
            except Exception as e:
                feat_id = feature.get("id", "unknown")
                errors.append(f"Feature {feat_id}: {str(e)}")
                logger.warning(f"Error processing feature {feat_id}: {e}")

        return {
            "total_features": len(features),
            "inserted": inserted,
            "updated": updated,
            "errors_count": len(errors),
            "errors": errors[:5],
        }


def ingest_usgs_feed(
    feed_url: Optional[str] = None, session: Optional[Session] = None
) -> Dict[str, Any]:
    """
    End-to-end synchronization: Fetches GeoJSON from USGS and persists in database.
    Ensures database tables are initialized.
    """
    init_db()
    geojson_data = usgs_client.fetch_feed(feed_url=feed_url)
    features = geojson_data.get("features", [])
    metadata = geojson_data.get("metadata", {})

    service = IngestionService()

    if session:
        result = service.ingest_features(features, session)
    else:
        with get_db() as db:
            result = service.ingest_features(features, db)

    result["feed_title"] = metadata.get("title", "USGS Feed")
    result["feed_url"] = metadata.get("url", feed_url or usgs_client.default_url)
    result["generated_at"] = parse_timestamp(metadata.get("generated"))
    return result
