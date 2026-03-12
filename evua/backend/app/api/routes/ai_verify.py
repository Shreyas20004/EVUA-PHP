"""
AI Verification API Routes
POST /api/ai/verify/{job_id}         — Start AI verification
GET  /api/ai/verify/{job_id}/results — Get AI verification results
POST /api/ai/verify/{section_id}/approve — Approve suggestion
POST /api/ai/verify/{section_id}/reject  — Reject suggestion
POST /api/ai/verify/{section_id}/apply   — Apply suggested fix
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ...schemas.ai_verify import (
    AIVerificationResponse,
    VerifyRequest,
    ApprovalRequest,
    VerificationSummaryResponse,
    AIIssue,
)
from ...services.ai_verification_service import get_ai_verification_service
from ...core.config import get_settings
from ...db import get_db
import asyncio

logger = logging.getLogger("evua.api.ai_verify")

router = APIRouter(prefix="/api/ai", tags=["ai_verification"])


@router.post("/verify/{job_id}", response_model=AIVerificationResponse)
async def verify_code(
    job_id: str,
    request: VerifyRequest,
    db: Session = Depends(get_db),
    settings = Depends(get_settings),
):
    """Verify migrated code through AI processing"""
    try:
        service = get_ai_verification_service(db, settings.gemini_api_key)

        result = await service.verify_file(
            job_id=job_id,
            file_path=request.file_path,
            original_code=request.original_code,
            migrated_code=request.migrated_code,
            risk_factors=request.risk_factors,
        )

        # Convert to response model
        return AIVerificationResponse(
            section_id=result['section_id'],
            file_path=result['file_path'],
            status=result['status'],
            ai_feedback=result['ai_feedback'],
            suggested_fix=result['suggested_fix'],
            confidence=result['confidence'],
            issues_found=[AIIssue(**issue) for issue in result.get('issues_found', [])],
            approved=False,
            review_timestamp=result['review_timestamp'],
        )
    except Exception as e:
        logger.error(f"Error verifying code: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-batch/{job_id}")
async def verify_batch(
    job_id: str,
    requests: list[VerifyRequest],
    db: Session = Depends(get_db),
    settings = Depends(get_settings),
):
    """Verify multiple files through AI (automatic for high-risk files)"""
    try:
        service = get_ai_verification_service(db, settings.gemini_api_key)
        results = []

        # Process sequentially to avoid rate limiting
        for req in requests:
            try:
                result = await service.verify_file(
                    job_id=job_id,
                    file_path=req.file_path,
                    original_code=req.original_code,
                    migrated_code=req.migrated_code,
                    risk_factors=req.risk_factors,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to verify {req.file_path}: {e}")
                results.append({
                    'file_path': req.file_path,
                    'status': 'error',
                    'error': str(e),
                })

        return {
            "status": "batch_verified",
            "job_id": job_id,
            "total": len(requests),
            "completed": len([r for r in results if r.get('status') == 'reviewed']),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Error verifying batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{job_id}/results", response_model=VerificationSummaryResponse)
async def get_verifications(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get all AI verifications for a job"""
    try:
        service = get_ai_verification_service(db=db)
        verifications = service.get_verifications(job_id)

        approved = sum(1 for v in verifications if v.get('approved'))
        rejected = sum(1 for v in verifications if v.get('review_status') == 'rejected')
        pending = len(verifications) - approved - rejected

        return VerificationSummaryResponse(
            job_id=job_id,
            total_verifications=len(verifications),
            approved=approved,
            rejected=rejected,
            pending=pending,
            verifications=[AIVerificationResponse(**v) if isinstance(v, dict) else v for v in verifications],
        )
    except Exception as e:
        logger.error(f"Error getting verifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/{section_id}/approve")
async def approve_suggestion(
    section_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve an AI suggestion"""
    try:
        service = get_ai_verification_service(db=db)
        success = service.approve_suggestion(section_id, request.reviewer_notes)

        if not success:
            raise HTTPException(status_code=404, detail="Verification not found")

        return {
            "status": "approved",
            "section_id": section_id,
            "message": "Suggestion approved",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/{section_id}/reject")
async def reject_suggestion(
    section_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db),
):
    """Reject an AI suggestion"""
    try:
        service = get_ai_verification_service(db=db)
        success = service.reject_suggestion(section_id, request.reviewer_notes)

        if not success:
            raise HTTPException(status_code=404, detail="Verification not found")

        return {
            "status": "rejected",
            "section_id": section_id,
            "message": "Suggestion rejected",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify/{section_id}/apply")
async def apply_fix(
    section_id: str,
    db: Session = Depends(get_db),
):
    """Apply an AI suggestion to the code"""
    try:
        service = get_ai_verification_service(db=db)
        fix = service.apply_fix(section_id)

        if not fix:
            raise HTTPException(status_code=404, detail="Suggestion or section not found")

        return {
            "status": "applied",
            "section_id": section_id,
            "corrected_code": fix,
            "message": "Fix applied successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying fix: {e}")
        raise HTTPException(status_code=500, detail=str(e))
