"""
Version Control API Routes
GET  /api/versions/{job_id}/history    — Get all versions
POST /api/versions/{job_id}/create     — Create a new version
GET  /api/versions/{job_id}/diff       — Get diff between versions
POST /api/versions/{job_id}/revert     — Preview and apply revert
GET  /api/versions/{job_id}/file       — Get file at specific version
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ...schemas.version import (
    VersionHistoryResponse,
    VersionSnapshotResponse,
    CreateVersionRequest,
    RevertPreviewResponse,
    RevertChangeInfo,
    DiffResponse,
    VersionFileResponse,
)
from ...services.version_control_service import get_version_control_service

logger = logging.getLogger("evua.api.versions")

router = APIRouter(prefix="/api/versions", tags=["version_control"])
vc_service = get_version_control_service()


@router.post("/{job_id}/init")
async def init_version_control(job_id: str):
    """Initialize version control for a migration job"""
    try:
        repo_path = vc_service.init_repo(job_id)
        return {
            "job_id": job_id,
            "status": "initialized",
            "repo_path": repo_path,
        }
    except Exception as e:
        logger.error(f"Error initializing version control: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/history", response_model=VersionHistoryResponse)
async def get_version_history(job_id: str):
    """Get complete version history for a job"""
    try:
        if not vc_service.repo_exists(job_id):
            raise HTTPException(status_code=404, detail=f"No version history for job {job_id}")

        versions = vc_service.get_versions(job_id)
        return VersionHistoryResponse(
            job_id=job_id,
            versions=[VersionSnapshotResponse(**v) for v in versions],
            total_versions=len(versions),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting version history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/create", response_model=dict)
async def create_version(job_id: str, request: CreateVersionRequest):
    """Create a new version (commit) for a job"""
    try:
        commit_hash = vc_service.create_version(
            job_id=job_id,
            message=request.message,
            stage=request.stage,
            files_changed=request.files_changed,
        )

        if not commit_hash:
            return {
                "status": "no_changes",
                "message": "No changes to commit",
            }

        return {
            "status": "created",
            "commit_hash": commit_hash,
            "message": request.message,
        }
    except Exception as e:
        logger.error(f"Error creating version: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/diff", response_model=DiffResponse)
async def get_diff(
    job_id: str,
    from_commit: Optional[str] = Query(None),
    to_commit: Optional[str] = Query(None),
):
    """Get unified diff between two commits"""
    try:
        diff_content = vc_service.get_diff(job_id, from_commit, to_commit or "HEAD")
        return DiffResponse(
            from_commit=from_commit,
            to_commit=to_commit or "HEAD",
            diff=diff_content,
        )
    except Exception as e:
        logger.error(f"Error getting diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/file-diff", response_model=DiffResponse)
async def get_file_diff(
    job_id: str,
    file_path: str = Query(...),
    from_commit: Optional[str] = Query(None),
    to_commit: Optional[str] = Query(None),
):
    """Get diff for a specific file between commits"""
    try:
        diff_content = vc_service.get_file_diff(
            job_id,
            file_path,
            from_commit,
            to_commit or "HEAD",
        )
        return DiffResponse(
            from_commit=from_commit,
            to_commit=to_commit or "HEAD",
            diff=diff_content,
        )
    except Exception as e:
        logger.error(f"Error getting file diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/revert-preview", response_model=RevertPreviewResponse)
async def preview_revert(
    job_id: str,
    target_commit: str = Query(...),
):
    """Preview what will change if reverting to a commit"""
    try:
        changes = vc_service.get_changes_for_revert(job_id, target_commit)
        return RevertPreviewResponse(
            job_id=job_id,
            target_commit=target_commit,
            changes=RevertChangeInfo(**changes),
        )
    except Exception as e:
        logger.error(f"Error previewing revert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/revert")
async def revert_to_version(
    job_id: str,
    target_commit: str = Query(...),
):
    """Apply revert to a previous commit (creates new commit)"""
    try:
        new_commit = vc_service.revert_to_version(job_id, target_commit)
        return {
            "status": "reverted",
            "from_commit": target_commit,
            "to_commit": new_commit,
            "message": f"Reverted to {target_commit}",
        }
    except Exception as e:
        logger.error(f"Error reverting: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/file", response_model=VersionFileResponse)
async def get_version_file(
    job_id: str,
    file_path: str = Query(...),
    commit: Optional[str] = Query(None),
):
    """Get file content at a specific version"""
    try:
        content = vc_service.get_file(job_id, file_path, commit)
        return VersionFileResponse(
            job_id=job_id,
            file_path=file_path,
            commit=commit,
            content=content,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
