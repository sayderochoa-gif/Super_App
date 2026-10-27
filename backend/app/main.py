"""
SismoWatch Backend API Entrypoint.
Production-grade FastAPI application with async database session lifecycle,
CORS security headers, automated seed bootstrap, and centralized error handling.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, async_engine, Base
from app.models.user import User
from app.security import get_password_hash
from app.routers import (
    auth,
    kpis,
    events,
    stats,
    reports,
    stream,
    pipeline,
    admin,
    agent
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sismowatch.main")


async def seed_default_users():
    """
    Seeds initial Admin and Viewer accounts from environment variables
    if they do not already exist. Passwords are never hardcoded in source.
    """
    async with AsyncSessionLocal() as session:
        try:
            # 1. Admin Seed
            admin_user_stmt = select(User).where(User.username == settings.ADMIN_USER.strip().lower())
            admin_res = await session.execute(admin_user_stmt)
            admin_exists = admin_res.scalar_one_or_none()

            if not admin_exists:
                admin_obj = User(
                    username=settings.ADMIN_USER.strip().lower(),
                    hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                    role="admin",
                    is_active=True
                )
                session.add(admin_obj)
                logger.info(f"Seeded default Admin account: {settings.ADMIN_USER}")

            # 2. Viewer Seed
            viewer_user_stmt = select(User).where(User.username == settings.VIEWER_USER.strip().lower())
            viewer_res = await session.execute(viewer_user_stmt)
            viewer_exists = viewer_res.scalar_one_or_none()

            if not viewer_exists:
                viewer_obj = User(
                    username=settings.VIEWER_USER.strip().lower(),
                    hashed_password=get_password_hash(settings.VIEWER_PASSWORD),
                    role="viewer",
                    is_active=True
                )
                session.add(viewer_obj)
                logger.info(f"Seeded default Viewer account: {settings.VIEWER_USER}")

            await session.commit()
        except Exception as exc:
            logger.warning(f"Note on initial seed (tables may be managed by init-db.sql): {exc}")
            await session.rollback()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: sets up DB connection and seeds users on startup."""
    logger.info("Initializing SismoWatch Backend Service...")
    try:
        # Seed users if database is reachable
        await seed_default_users()
    except Exception as exc:
        logger.warning(f"Startup database check: {exc}")
    yield
    logger.info("Shutting down SismoWatch Backend Service...")
    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SismoWatch Data Lakehouse & AI Analytics Platform",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."}
    )


# Health Check
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Include Routers
app.include_router(auth.router)
app.include_router(kpis.router)
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(reports.router)
app.include_router(stream.router)
app.include_router(pipeline.router)
app.include_router(admin.router)
app.include_router(agent.router)
