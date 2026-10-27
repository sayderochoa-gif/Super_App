"""HTTP Client for consuming the USGS Earthquake API (GeoJSON feeds)."""

import logging
from typing import Any, Dict, Optional
import requests
from agentebot.config import settings

logger = logging.getLogger(__name__)

# Standard USGS GeoJSON feed endpoints
USGS_FEEDS = {
    "all_hour": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
    "all_day": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson",
    "all_week": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson",
    "all_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson",
    "significant_month": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",
}


class USGSClient:
    """Client for fetching earthquake GeoJSON data from USGS feeds."""

    def __init__(self, default_url: Optional[str] = None, timeout: int = 15):
        self.default_url = default_url or settings.USGS_FEED_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "SeismicRelationalAgent/1.0 (EarthquakeMonitoring)",
            "Accept": "application/json",
        })

    def fetch_feed(self, feed_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch earthquake GeoJSON from the given or configured feed URL.

        Args:
            feed_url: Optional specific GeoJSON endpoint or feed key.
                      If not provided, uses default_url.

        Returns:
            Dict containing the parsed GeoJSON payload.

        Raises:
            requests.RequestException: If network or HTTP error occurs.
            ValueError: If payload is not valid GeoJSON.
        """
        target_url = feed_url or self.default_url
        if target_url in USGS_FEEDS:
            target_url = USGS_FEEDS[target_url]

        logger.info(f"Fetching USGS earthquake feed from: {target_url}")
        response = self.session.get(target_url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
            raise ValueError(
                f"Invalid GeoJSON payload received. Expected type 'FeatureCollection', got: {data.get('type')}"
            )

        features_count = len(data.get("features", []))
        logger.info(f"Successfully retrieved {features_count} earthquake features from USGS.")
        return data


# Default singleton instance
usgs_client = USGSClient()
