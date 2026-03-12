"""
Application Settings
Loaded from environment variables (or a .env file via python-dotenv).
"""
from functools import lru_cache
from typing import Optional
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Default storage root: /app/storage in Docker, backend/storage locally
_default_storage_dir = os.environ.get(
    "STORAGE_DIR",
    str(Path(__file__).resolve().parents[2] / "storage")
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- API credentials ----------
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # ---------- Upload limits ----------
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")

    # ---------- Pipeline ----------
    max_concurrency: int = Field(default=5, alias="MAX_CONCURRENCY")
    use_mock_ai: bool = Field(default=False, alias="USE_MOCK_AI")

    # ---------- CORS ----------
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    # ---------- Misc ----------
    debug: bool = Field(default=False, alias="DEBUG")

    # ---------- Storage ----------
    storage_dir: str = Field(default=_default_storage_dir, alias="STORAGE_DIR")

    @property
    def upload_dir(self) -> str:
        return str(Path(self.storage_dir) / "uploads")

    @property
    def versions_dir(self) -> str:
        return str(Path(self.storage_dir) / "versions")

    @property
    def db_path(self) -> str:
        return str(Path(self.storage_dir) / "evua.db")

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
