"""
Migration Service
Wraps the engine's MigrationPipeline and bridges it to the FastAPI layer.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("evua.migration_service")

# ---------------------------------------------------------------------------
# Engine import: works both in local dev and inside Docker
# The engine/ directory sits at the project root (sibling of backend/).
# We add the project root to sys.path so `import engine` works.
# ---------------------------------------------------------------------------
# Walk up from this file until we find the directory containing engine/
_srv = Path(__file__).resolve()
_project_root = next(
    (p for p in _srv.parents if (p / "engine").is_dir()),
    _srv.parents[2],  # Fallback: /app/ in Docker (PYTHONPATH already handles it)
)
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from engine.pipeline import MigrationPipeline                          # noqa: E402
from engine.models.migration_models import (                           # noqa: E402
    PHPVersion,
    PipelineResult,
    MigrationResult,
)
from engine.utils.file_scanner import FileScanner                      # noqa: E402

from ..schemas.migration import (
    FileResultResponse,
    IssueResponse,
    JobStatus,
    JobStatusResponse,
    RuleMatchResponse,
)
from ..workers.job_queue import job_queue, JobState
from .version_control_service import get_version_control_service as _get_vc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _php_version(value: str) -> PHPVersion:
    return PHPVersion(value)


def _build_file_result(res: MigrationResult) -> FileResultResponse:
    return FileResultResponse(
        file_path=res.file_path,
        status=res.status.value,
        original_code=res.original_code,  # Include full source for Monaco viewer
        migrated_code=res.migrated_code,  # Include full source for Monaco viewer
        original_size=len(res.original_code.encode("utf-8")),
        migrated_size=len(res.migrated_code.encode("utf-8")),
        rule_matches=[
            RuleMatchResponse(
                rule_id=m.rule_id,
                rule_name=m.rule_name,
                matched_text=m.matched_text,
                start_line=m.start_line,
                end_line=m.end_line,
                replacement=m.replacement,
                confidence=m.confidence,
            )
            for m in res.rule_matches
        ],
        issues=[
            IssueResponse(
                rule_id=i.rule_id,
                severity=i.severity.value,
                message=i.message,
                line=i.line,
                col=i.col,
                original_code=i.original_code,
                suggested_fix=i.suggested_fix,
                auto_fixable=i.auto_fixable,
                requires_ai=i.requires_ai,
            )
            for i in res.issues
        ],
        ai_changes=res.ai_changes,
        diff=res.stats.get("diff", ""),
        errors=res.errors,
        stats={k: v for k, v in res.stats.items() if k != "diff"},
    )


# ---------------------------------------------------------------------------
# Core async migration coroutine
# ---------------------------------------------------------------------------

async def run_migration(
    job_id: str,
    file_paths: list[str],
    source_version: str,
    target_version: str,
    output_dir: Optional[str],
    dry_run: bool,
    use_mock_ai: bool,
    gemini_api_key: Optional[str],
) -> PipelineResult:
    """
    Run the migration pipeline for the given paths.
    Submitted to the job queue as a background coroutine.
    """
    src_ver = _php_version(source_version)
    tgt_ver = _php_version(target_version)

    pipeline = MigrationPipeline(
        source_version=src_ver,
        target_version=tgt_ver,
        gemini_api_key=gemini_api_key,
        dry_run=dry_run,
        use_mock_ai=use_mock_ai,
    )

    # Collect all PHP files from paths (files and/or directories)
    scanner = FileScanner()
    all_php_files: list[str] = scanner.scan_paths(file_paths)

    if not all_php_files:
        return PipelineResult(
            job_id=job_id,
            source_version=src_ver,
            target_version=tgt_ver,
            total_files=0,
            summary={"message": "No PHP files found in the provided paths"},
        )

    # --- Snapshot originals before migration ---
    vc = _get_vc()
    try:
        vc.init_repo(job_id)
        for fp in all_php_files:
            vc.save_file(job_id, fp, Path(fp).read_text(encoding="utf-8", errors="replace"))
        vc.create_version(job_id, f"Original PHP {source_version} source", stage="initial", files_changed=len(all_php_files))
    except Exception as _vc_err:
        logger.warning("Version control snapshot (before) failed: %s", _vc_err)

    # Use the pipeline's directory runner over each discovered file
    results = []
    import asyncio
    semaphore = asyncio.Semaphore(pipeline.max_concurrency)

    async def bounded(fp: str):
        async with semaphore:
            return await pipeline.run_file_async(fp)

    tasks = [bounded(fp) for fp in all_php_files]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    from engine.models.migration_models import MigrationStatus
    import uuid as _uuid

    pipeline_result = PipelineResult(
        job_id=job_id,
        source_version=src_ver,
        target_version=tgt_ver,
        total_files=len(all_php_files),
    )

    for fp, res in zip(all_php_files, raw_results):
        if isinstance(res, Exception):
            logger.error("Error processing %s: %s", fp, res)
            pipeline_result.failed += 1
            pipeline_result.results.append(
                MigrationResult(
                    file_path=fp,
                    original_code="",
                    migrated_code="",
                    status=MigrationStatus.FAILED,
                    errors=[str(res)],
                )
            )
        else:
            pipeline_result.results.append(res)
            if res.status == MigrationStatus.FAILED:
                pipeline_result.failed += 1
            elif res.status == MigrationStatus.SKIPPED:
                pipeline_result.skipped += 1
            else:
                pipeline_result.completed += 1

            if output_dir and not dry_run:
                pipeline._write_output(fp, str(Path(fp).parent), output_dir, res.migrated_code)

    pipeline_result.summary = pipeline._summarise(pipeline_result)

    # --- Snapshot migrated output after migration ---
    try:
        migrated_count = 0
        for res in pipeline_result.results:
            if res.migrated_code:
                vc.save_file(job_id, res.file_path, res.migrated_code)
                migrated_count += 1
        if migrated_count:
            vc.create_version(
                job_id,
                f"Migrated to PHP {target_version} ({migrated_count} files)",
                stage="migrated",
                files_changed=migrated_count,
            )
    except Exception as _vc_err:
        logger.warning("Version control snapshot (after) failed: %s", _vc_err)

    return pipeline_result


# ---------------------------------------------------------------------------
# Job status helper
# ---------------------------------------------------------------------------

def get_job_status_response(job_id: str) -> Optional[JobStatusResponse]:
    """Convert internal job state to the API response schema."""
    job = job_queue.get_job(job_id)
    if job is None:
        return None

    status_map = {
        JobState.PENDING: JobStatus.PENDING,
        JobState.RUNNING: JobStatus.RUNNING,
        JobState.COMPLETED: JobStatus.COMPLETED,
        JobState.FAILED: JobStatus.FAILED,
    }

    resp = JobStatusResponse(
        job_id=job_id,
        status=status_map[job.state],
        error=job.error,
    )

    if job.result is not None:
        pipeline_result: PipelineResult = job.result
        resp.total_files = pipeline_result.total_files
        resp.completed = pipeline_result.completed
        resp.failed = pipeline_result.failed
        resp.skipped = pipeline_result.skipped
        resp.summary = pipeline_result.summary
        resp.results = [_build_file_result(r) for r in pipeline_result.results]

    return resp
