"""
SQLAlchemy ORM Models for Migration, Version Control, and Risk Assessment
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .database import Base


class MigrationJobModel(Base):
    """Tracks migration jobs and their metadata"""
    __tablename__ = 'migration_jobs'

    job_id = Column(String(36), primary_key=True, index=True)
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    source_version = Column(String(10))  # 5.6, 7.0, 7.4, 8.0, 8.1, 8.2, 8.3
    target_version = Column(String(10))

    total_files = Column(Integer, default=0)
    completed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    skipped_files = Column(Integer, default=0)

    git_repo_path = Column(String(500), nullable=True)  # Path to git repo
    error_message = Column(Text, nullable=True)
    summary = Column(JSON, default=dict)  # Summary stats

    # Relationships
    versions = relationship('VersionSnapshotModel', back_populates='job', cascade='all, delete-orphan')
    risk_assessments = relationship('RiskAssessmentModel', back_populates='job', cascade='all, delete-orphan')
    ai_verifications = relationship('AIVerificationModel', back_populates='job', cascade='all, delete-orphan')


class VersionSnapshotModel(Base):
    """Git commit snapshots for version control"""
    __tablename__ = 'version_snapshots'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey('migration_jobs.job_id'), index=True)

    commit_hash = Column(String(40), unique=True, index=True)  # Git commit SHA
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    commit_message = Column(Text)
    author = Column(String(100), default='evua')  # Commit author

    files_changed = Column(Integer)  # Number of files in this commit
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    migration_stage = Column(String(50))  # 'initial', 'risk_assessed', 'ai_verified', 'reverted'
    extra_data = Column(JSON, default=dict)  # Additional info

    # Relationship
    job = relationship('MigrationJobModel', back_populates='versions')


class RiskAssessmentModel(Base):
    """Risk scores and metrics for each file"""
    __tablename__ = 'risk_assessments'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey('migration_jobs.job_id'), index=True)

    file_path = Column(String(500), index=True)
    assessment_time = Column(DateTime, default=datetime.utcnow, index=True)

    # Risk metrics (0.0 - 1.0)
    overall_score = Column(Float)  # 0-1 risk score
    complexity_score = Column(Float)
    dependency_score = Column(Float)
    pattern_score = Column(Float)
    ai_confidence_score = Column(Float)
    change_size_score = Column(Float)
    issue_count_score = Column(Float)

    risk_category = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL

    # Detailed metrics
    lines_of_code = Column(Integer)
    nesting_depth = Column(Integer)
    function_count = Column(Integer)
    issue_count = Column(Integer)

    detailed_factors = Column(JSON, default=dict)  # Breakdown of risk factors
    recommendations = Column(JSON, default=list)  # Suggested actions

    # Relationship
    job = relationship('MigrationJobModel', back_populates='risk_assessments')


class AIVerificationModel(Base):
    """AI review feedback and suggestions for high-risk code"""
    __tablename__ = 'ai_verifications'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey('migration_jobs.job_id'), index=True)

    file_path = Column(String(500), index=True)
    section_id = Column(String(100))  # Unique identifier within file

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Code sections
    original_code = Column(Text)  # Original PHP code
    migrated_code = Column(Text)  # Migrated PHP code

    # AI Review
    review_status = Column(String(50), default='pending')  # pending, reviewed, accepted, rejected
    ai_feedback = Column(Text)  # AI's analysis and feedback
    suggested_fix = Column(Text)  # AI's recommended fix

    # Manual review
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by_user = Column(Boolean, default=False)

    # Applied fix tracking
    fix_applied = Column(Boolean, default=False)
    fix_applied_at = Column(DateTime, nullable=True)

    # Metadata
    confidence_score = Column(Float)  # AI confidence in suggestion (0-1)
    issues_found = Column(JSON, default=list)  # List of detected issues
    extra_data = Column(JSON, default=dict)

    # Relationship
    job = relationship('MigrationJobModel', back_populates='ai_verifications')


class ChangeHistoryModel(Base):
    """Audit trail of all changes made to migration"""
    __tablename__ = 'change_history'

    id = Column(Integer, primary_key=True)
    job_id = Column(String(36), ForeignKey('migration_jobs.job_id'), index=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action = Column(String(100))  # 'migrated', 'risk_assessed', 'ai_verified', 'reverted', 'approved'

    file_path = Column(String(500), nullable=True)
    description = Column(Text)

    performed_by = Column(String(100), default='system')
    extra_data = Column(JSON, default=dict)  # Additional context
