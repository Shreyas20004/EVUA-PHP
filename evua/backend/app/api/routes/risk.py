"""
Risk Assessment API Routes
POST /api/risk/assess      — Assess risk for files in a job
GET  /api/risk/{job_id}/summary  — Get risk summary
GET  /api/risk/{job_id}/critical — Get files needing AI review
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ...schemas.risk import (
    FileRiskResponse,
    RiskSummaryResponse,
    CriticalFilesResponse,
    AssessRequest,
)
from ...services.risk_assessment_service import get_risk_assessment_service
from ...db import get_db

logger = logging.getLogger("evua.api.risk")

router = APIRouter(prefix="/api/risk", tags=["risk_assessment"])


@router.post("/assess")
async def assess_risk(
    job_id: str,
    request: AssessRequest,
    db: Session = Depends(get_db),
):
    """Assess risk for a single file in a migration job"""
    try:
        service = get_risk_assessment_service(db)
        result = service.assess_file(
            job_id=job_id,
            file_path=request.file_path,
            original_code=request.original_code,
            migrated_code=request.migrated_code,
            issue_count=request.issue_count,
            ai_confidence=request.ai_confidence,
        )
        return FileRiskResponse(**result)
    except Exception as e:
        logger.error(f"Error assessing risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assess-job/{job_id}")
async def assess_job_risk(
    job_id: str,
    assessments: list[AssessRequest],
    db: Session = Depends(get_db),
):
    """Assess risk for all files in a job"""
    try:
        service = get_risk_assessment_service(db)
        results = []

        for req in assessments:
            result = service.assess_file(
                job_id=job_id,
                file_path=req.file_path,
                original_code=req.original_code,
                migrated_code=req.migrated_code,
                issue_count=req.issue_count,
                ai_confidence=req.ai_confidence,
            )
            results.append(FileRiskResponse(**result))

        return {
            "status": "assessed",
            "job_id": job_id,
            "total_assessments": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error assessing job risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/summary", response_model=RiskSummaryResponse)
async def get_risk_summary(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get risk assessment summary for a job"""
    try:
        service = get_risk_assessment_service(db)
        summary = service.get_job_risk_summary(job_id)

        if not summary:
            raise HTTPException(status_code=404, detail=f"No risk data for job {job_id}")

        # Convert to response model
        files = [FileRiskResponse(**f) if isinstance(f, dict) else f for f in summary.get('files', [])]
        summary['files'] = files

        return RiskSummaryResponse(**summary)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}/critical", response_model=CriticalFilesResponse)
async def get_critical_files(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get files with HIGH or CRITICAL risk (for AI verification)"""
    try:
        service = get_risk_assessment_service(db)
        critical = service.get_critical_files(job_id)

        return CriticalFilesResponse(
            job_id=job_id,
            critical_files=critical,
            count=len(critical),
        )
    except Exception as e:
        logger.error(f"Error getting critical files: {e}")
        raise HTTPException(status_code=500, detail=str(e))
