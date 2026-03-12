"""
Pydantic request / response models for the migration API.
"""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums mirrored from engine so the API is self-contained
# ---------------------------------------------------------------------------

class PHPVersionEnum(str, Enum):
    PHP_5_6 = "5.6"
    PHP_7_0 = "7.0"
    PHP_7_4 = "7.4"
    PHP_8_0 = "8.0"
    PHP_8_1 = "8.1"
    PHP_8_2 = "8.2"
    PHP_8_3 = "8.3"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class MigrateRequest(BaseModel):
    source_version: PHPVersionEnum = Field(
        ..., description="PHP version to migrate FROM"
    )
    target_version: PHPVersionEnum = Field(
        ..., description="PHP version to migrate TO"
    )
    file_paths: list[str] = Field(
        ..., description="Absolute paths to PHP files or directories"
    )
    output_dir: Optional[str] = Field(
        default=None, description="Where to write migrated files (optional)"
    )
    dry_run: bool = Field(
        default=False,
        description="If true, rules are checked but no files are modified",
    )
    use_mock_ai: bool = Field(
        default=False,
        description="Use mock AI instead of Gemini (for testing)",
    )


# ---------------------------------------------------------------------------
# Inner response models
# ---------------------------------------------------------------------------

class RuleMatchResponse(BaseModel):
    rule_id: str
    rule_name: str
    matched_text: str
    start_line: int
    end_line: int
    replacement: Optional[str] = None
    confidence: float = 1.0


class IssueResponse(BaseModel):
    rule_id: str
    severity: str
    message: str
    line: int
    col: int
    original_code: str
    suggested_fix: Optional[str] = None
    auto_fixable: bool
    requires_ai: bool


class FileResultResponse(BaseModel):
    file_path: str
    status: str
    original_code: str = ""  # Original PHP code (for Monaco diff viewer)
    migrated_code: str = ""  # Migrated PHP code (for Monaco diff viewer)
    original_size: int
    migrated_size: int
    rule_matches: list[RuleMatchResponse] = []
    issues: list[IssueResponse] = []
    ai_changes: list[dict] = []
    diff: str = ""
    errors: list[str] = []
    stats: dict = {}


# ---------------------------------------------------------------------------
# Top-level response models
# ---------------------------------------------------------------------------

class MigrateResponse(BaseModel):
    """Returned immediately when a job is created."""
    job_id: str
    status: JobStatus
    message: str = "Migration job queued"


class JobStatusResponse(BaseModel):
    """Returned when polling job status."""
    job_id: str
    status: JobStatus
    total_files: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[FileResultResponse] = []
    summary: dict = {}
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Upload models
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    upload_id: str
    files: list[str]
    message: str = "Files uploaded successfully"
