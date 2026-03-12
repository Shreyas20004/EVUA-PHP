"""
SQLite Database Connection and Session Management
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database path - respects STORAGE_DIR env var for Docker compatibility
# In Docker: /app/storage   |   Locally: backend/storage/
_storage_dir = os.environ.get(
    "STORAGE_DIR",
    str(Path(__file__).resolve().parents[2] / "storage")
)
os.makedirs(_storage_dir, exist_ok=True)

DATABASE_URL = f'sqlite:///{_storage_dir}/evua.db'

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    echo=False  # Set DEBUG=true to enable SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


def get_db():
    """Dependency injection for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
