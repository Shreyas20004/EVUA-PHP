"""
AI Verification Schemas
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class AIIssue(BaseModel):
    """Issue found by AI"""
    severity: str  # critical, high, medium, low
    description: str
    line: Optional[int] = None


class AIVerificationResponse(BaseModel):
    """AI verification result"""
    section_id: str
    file_path: str
    status: str  # reviewed, pending, accepted, rejected
    ai_feedback: str
    suggested_fix: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    issues_found: List[AIIssue] = []
    approved: bool = False
    review_timestamp: str


class VerifyRequest(BaseModel):
    """Request to verify migrated code"""
    file_path: str
    original_code: str
    migrated_code: str
    risk_factors: Optional[Dict] = None


class ApprovalRequest(BaseModel):
    """Request to approve a suggestion"""
    reviewer_notes: Optional[str] = None


class VerificationSummaryResponse(BaseModel):
    """Summary of all verifications for a job"""
    job_id: str
    total_verifications: int
    approved: int
    rejected: int
    pending: int
    verifications: List[AIVerificationResponse]
