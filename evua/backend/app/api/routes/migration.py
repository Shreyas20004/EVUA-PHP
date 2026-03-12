"""
Migration routes
POST /api/migrate      — create a migration job
GET  /api/jobs/{id}    — poll job status
GET  /api/jobs         — list all jobs
"""
from fastapi import APIRouter, HTTPException

from ...core.dependencies import SettingsDep
from ...schemas.migration import (
    JobStatus,
    JobStatusResponse,
    MigrateRequest,
    MigrateResponse,
)
from ...services.migration_service import get_job_status_response, run_migration
from ...workers.job_queue import job_queue

router = APIRouter(prefix="/api", tags=["migration"])


@router.post("/migrate", response_model=MigrateResponse, status_code=202)
async def create_migration_job(
    request: MigrateRequest,
    settings: SettingsDep,
):
    """
    Kick off an async migration job.
    Returns ``job_id`` immediately — poll ``GET /api/jobs/{job_id}`` for results.
    """
    job_id = job_queue.create_job()

    coro = run_migration(
        job_id=job_id,
        file_paths=request.file_paths,
        source_version=request.source_version.value,
        target_version=request.target_version.value,
        output_dir=request.output_dir,
        dry_run=request.dry_run,
        use_mock_ai=request.use_mock_ai or settings.use_mock_ai,
        gemini_api_key=settings.gemini_api_key,
    )
    job_queue.submit(job_id, coro)

    return MigrateResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Migration job queued",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str):
    """Poll the status and results of a migration job."""
    resp = get_job_status_response(job_id)
    if resp is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return resp


@router.get("/jobs")
async def list_jobs():
    """Return a summary list of all in-memory jobs."""
    return [
        {"job_id": j.job_id, "status": j.state.value, "error": j.error}
        for j in job_queue.all_jobs()
    ]
