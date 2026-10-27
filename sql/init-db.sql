-- =============================================================================
-- SISMAWATCH (SUPERAPP) - DATABASE INITIALIZATION SCRIPT
-- =============================================================================
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS curated;

-- -----------------------------------------------------------------------------
-- ROLES & LEAST PRIVILEGE CONFIGURATION
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ingest_user') THEN
        CREATE ROLE ingest_user WITH LOGIN PASSWORD 'ingest_secret_pass';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'transform_user') THEN
        CREATE ROLE transform_user WITH LOGIN PASSWORD 'transform_secret_pass';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user WITH LOGIN PASSWORD 'app_secret_pass';
    END IF;
END $$;

-- Schema Permissions
GRANT USAGE ON SCHEMA raw TO ingest_user, transform_user;
GRANT USAGE ON SCHEMA staging TO transform_user;
GRANT USAGE ON SCHEMA curated TO transform_user, app_user;

-- -----------------------------------------------------------------------------
-- RAW LAYER
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.earthquake_feeds (
    id SERIAL PRIMARY KEY,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL
);

-- Ingest User: INSERT-only on raw
GRANT INSERT ON raw.earthquake_feeds TO ingest_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO ingest_user;

-- Transform User: SELECT on raw
GRANT SELECT ON raw.earthquake_feeds TO transform_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA raw TO transform_user;

-- -----------------------------------------------------------------------------
-- STAGING LAYER
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staging.earthquakes (
    id VARCHAR(100) PRIMARY KEY,
    mag FLOAT,
    place TEXT,
    time TIMESTAMPTZ,
    updated TIMESTAMPTZ,
    tz INT,
    url TEXT,
    detail TEXT,
    felt INT,
    cdi FLOAT,
    mmi FLOAT,
    alert TEXT,
    status VARCHAR(50),
    tsunami INT,
    sig INT,
    net VARCHAR(50),
    code VARCHAR(50),
    ids TEXT,
    sources TEXT,
    types TEXT,
    nst INT,
    dmin FLOAT,
    rms FLOAT,
    gap FLOAT,
    magType VARCHAR(50),
    type VARCHAR(50),
    title TEXT,
    longitude FLOAT,
    latitude FLOAT,
    depth_km FLOAT,
    processed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_staging_time ON staging.earthquakes (time DESC);
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO transform_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO transform_user;

-- -----------------------------------------------------------------------------
-- CURATED LAYER
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS curated.earthquakes (
    id VARCHAR(100) PRIMARY KEY,
    mag FLOAT NOT NULL,
    place TEXT,
    time TIMESTAMPTZ NOT NULL,
    updated TIMESTAMPTZ,
    tz INT,
    url TEXT,
    detail TEXT,
    felt INT,
    cdi FLOAT,
    mmi FLOAT,
    alert TEXT,
    status VARCHAR(50),
    tsunami INT DEFAULT 0,
    sig INT,
    net VARCHAR(50),
    code VARCHAR(50),
    ids TEXT,
    sources TEXT,
    types TEXT,
    nst INT,
    dmin FLOAT,
    rms FLOAT,
    gap FLOAT,
    magType VARCHAR(50),
    type VARCHAR(50),
    title TEXT,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    depth_km FLOAT NOT NULL,
    curated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_curated_time ON curated.earthquakes (time DESC);
CREATE INDEX IF NOT EXISTS idx_curated_mag ON curated.earthquakes (mag DESC);
CREATE INDEX IF NOT EXISTS idx_curated_lat_lon ON curated.earthquakes (latitude, longitude);

CREATE TABLE IF NOT EXISTS curated.quarantine (
    id SERIAL PRIMARY KEY,
    source_id VARCHAR(100),
    rejected_at TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT NOT NULL,
    raw_data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS curated.quality_audit (
    id SERIAL PRIMARY KEY,
    dag_run_id VARCHAR(255),
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    total_records INT NOT NULL,
    passed_records INT NOT NULL,
    rejected_records INT NOT NULL,
    quality_score FLOAT NOT NULL,
    rules_summary JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS curated.ai_daily_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE UNIQUE NOT NULL,
    narrative_text TEXT NOT NULL,
    structured_kpis JSONB NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    tokens_used INT DEFAULT 0,
    latency_sec FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS curated.ai_anomalies (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    anomaly_type VARCHAR(100) NOT NULL,
    metric_trigger TEXT NOT NULL,
    description TEXT NOT NULL,
    event_ids JSONB
);

-- Users & RBAC for Application
CREATE TABLE IF NOT EXISTS curated.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Permissions for Transform User
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA curated TO transform_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA curated TO transform_user;

-- Permissions for App User (ReadOnly on curated analytical tables, read-write on users for auth management)
GRANT SELECT ON curated.earthquakes TO app_user;
GRANT SELECT ON curated.quality_audit TO app_user;
GRANT SELECT ON curated.ai_daily_reports TO app_user;
GRANT SELECT ON curated.ai_anomalies TO app_user;
GRANT SELECT ON curated.quarantine TO app_user;
GRANT SELECT, INSERT, UPDATE ON curated.users TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA curated TO app_user;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA raw GRANT SELECT ON TABLES TO transform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging GRANT ALL ON TABLES TO transform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated GRANT ALL ON TABLES TO transform_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA curated GRANT SELECT ON TABLES TO app_user;
