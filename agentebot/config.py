"""Configuration settings for the Seismic Monitoring Relational Agent."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration and environment variables."""

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'seismic_agent.db'}"

    # USGS Feed Endpoint
    USGS_FEED_URL: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

    # OpenAI / LLM Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Logging & Runtime
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_database_url(self) -> str:
        """Resolve SQLite relative path against BASE_DIR to ensure consistency."""
        url = self.DATABASE_URL
        if ":memory:" in url:
            return url
        if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
            rel_path = url.replace("sqlite:///", "")
            if not os.path.isabs(rel_path):
                return f"sqlite:///{(BASE_DIR / rel_path).resolve()}"
        return url


settings = Settings()
