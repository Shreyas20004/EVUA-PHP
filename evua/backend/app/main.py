"""
evua — FastAPI Application Entry Point
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .api.routes import health, migration, files, versions, risk, ai_verify
from .db import init_db

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if get_settings().debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("evua.app")


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown hooks)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Create all required storage directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.versions_dir, exist_ok=True)
    logger.info("Storage dirs: %s", settings.storage_dir)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized: %s", settings.db_path)
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

    logger.info("evua backend started")
    yield
    logger.info("evua backend shutting down.")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="evua — PHP Migration API",
        description=(
            "Hybrid rule-based + AI-powered PHP version migration engine.\n\n"
            "Upload PHP files, specify source and target versions, and retrieve "
            "fully migrated code with a detailed change report."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ---- CORS ----
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- Routers ----
    app.include_router(health.router)
    app.include_router(migration.router)
    app.include_router(files.router)
    app.include_router(versions.router)
    app.include_router(risk.router)
    app.include_router(ai_verify.router)

    return app


app = create_app()
