"""
Risk Assessment API Schemas
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RiskFactorResponse(BaseModel):
    """Risk score breakdown"""
    complexity: float
    dependencies: float
    patterns: float
    changes: float
    issues: float


class RiskMetricsResponse(BaseModel):
    """Code complexity metrics"""
    lines_of_code: int
    nesting_depth: int
    function_count: int
    issue_count: int


class FileRiskResponse(BaseModel):
    """Risk assessment for a file"""
    file_path: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    risk_category: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    factors: RiskFactorResponse
    metrics: RiskMetricsResponse
    recommendations: List[str]


class RiskSummaryResponse(BaseModel):
    """Risk summary for an entire job"""
    job_id: str
    total_files: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    average_score: float
    files: List[FileRiskResponse]


class CriticalFilesResponse(BaseModel):
    """Files requiring AI verification"""
    job_id: str
    critical_files: List[Dict] = Field(..., description="List of high/critical risk files")
    count: int


class AssessRequest(BaseModel):
    """Request to assess risk for a file"""
    file_path: str
    original_code: str
    migrated_code: str
    issue_count: int = Field(default=0)
    ai_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
