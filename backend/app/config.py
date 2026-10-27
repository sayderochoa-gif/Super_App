"""
Backend Configuration via Pydantic Settings.
Reads environment variables for database connections, JWT secrets,
Airflow integration, and initial seed credentials.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App General
    PROJECT_NAME: str = "SismoWatch API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # CORS Origins (comma-separated or list)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost,http://127.0.0.1:5173"

    # Database Configuration
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "sismowatch"
    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_secret_pass"
    DATABASE_URL: str = ""

    # JWT Authentication
    JWT_SECRET_KEY: str = "sismowatch-super-secret-jwt-key-2025-production-grade"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Seed Admin & Viewer Credentials (Never hardcoded in plain code, fed via env)
    ADMIN_USER: str = "admin@sismowatch.com"
    ADMIN_PASSWORD: str = "AdminSismoWatch2025!"
    VIEWER_USER: str = "viewer@sismowatch.com"
    VIEWER_PASSWORD: str = "ViewerSismoWatch2025!"

    # Airflow Integration
    AIRFLOW_BASE_URL: str = "http://airflow-webserver:8080"
    AIRFLOW_USERNAME: str = "airflow"
    AIRFLOW_PASSWORD: str = "airflow"

    # External AI
    OPENAI_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def get_sync_database_url(self) -> str:
        if self.DATABASE_URL:
            # If postgresql:// without driver, ensure psycopg2
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
            if self.DATABASE_URL.startswith("postgresql://") and not self.DATABASE_URL.startswith("postgresql+"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
            return self.DATABASE_URL
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def get_async_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
            return url
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
