"""
Version Control API Schemas
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class VersionSnapshotResponse(BaseModel):
    """Single version/commit in the history"""
    index: int
    hash: str = Field(..., description="Git commit hash")
    message: str = Field(..., description="Commit message")
    author: str = Field(..., description="Commit author")
    timestamp: str = Field(..., description="ISO format timestamp")
    files_changed: int = Field(..., description="Number of files in this commit")
    insertions: int = Field(..., description="Total line insertions")
    deletions: int = Field(..., description="Total line deletions")


class VersionHistoryResponse(BaseModel):
    """History of all versions for a job"""
    job_id: str
    versions: List[VersionSnapshotResponse]
    total_versions: int


class CreateVersionRequest(BaseModel):
    """Request to create a new version"""
    message: str = Field(..., description="Commit message")
    stage: str = Field(default='migration', description="Migration stage")
    files_changed: Optional[int] = Field(None, description="Number of files changed")


class RevertChangeInfo(BaseModel):
    """Information about changes that would be reverted"""
    added_files: List[str] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    deleted_files: List[str] = Field(default_factory=list)
    total_changes: int


class RevertPreviewResponse(BaseModel):
    """Preview of revert operation"""
    job_id: str
    target_commit: str
    changes: RevertChangeInfo


class DiffResponse(BaseModel):
    """Unified diff output"""
    from_commit: Optional[str] = None
    to_commit: str = "HEAD"
    diff: str = Field(..., description="Unified diff content")


class VersionFileResponse(BaseModel):
    """File content at a specific version"""
    job_id: str
    file_path: str
    commit: Optional[str] = None
    content: str
