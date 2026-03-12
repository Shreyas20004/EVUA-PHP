"""
Risk Assessment Service
Evaluates risk for migrated PHP code
"""
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from ..db import SessionLocal, RiskAssessmentModel, MigrationJobModel
from ..utils.risk_metrics import RiskMetricsCalculator

logger = logging.getLogger("evua.risk_assessment_service")


class RiskAssessmentService:
    """Assess and track risk for migration jobs"""

    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()

    def assess_file(
        self,
        job_id: str,
        file_path: str,
        original_code: str,
        migrated_code: str,
        issue_count: int = 0,
        ai_confidence: float = 1.0,
    ) -> Dict:
        """
        Assess risk for a single file.

        Returns:
            Dict with risk metrics and score
        """
        try:
            # Calculate risk factors
            factors = RiskMetricsCalculator.calculate_scores(
                original_code,
                migrated_code,
                issue_count,
                ai_confidence,
            )

            # Calculate overall score
            overall_score, risk_category = RiskMetricsCalculator.calculate_overall_risk(
                factors,
                ai_confidence,
            )

            # Get recommendations
            recommendations = RiskMetricsCalculator.get_risk_recommendations(factors, risk_category)

            # Measure complexity
            loc, nesting, func_count = RiskMetricsCalculator.measure_complexity(migrated_code)

            # Store in database
            assessment = RiskAssessmentModel(
                job_id=job_id,
                file_path=file_path,
                overall_score=overall_score,
                risk_category=risk_category,
                complexity_score=factors.complexity_score,
                dependency_score=factors.dependency_score,
                pattern_score=factors.pattern_complexity_score,
                ai_confidence_score=ai_confidence,
                change_size_score=factors.change_size_score,
                issue_count_score=factors.issue_score,
                lines_of_code=loc,
                nesting_depth=nesting,
                function_count=func_count,
                issue_count=issue_count,
                detailed_factors={
                    'complexity': factors.complexity_score,
                    'dependencies': factors.dependency_score,
                    'patterns': factors.pattern_complexity_score,
                    'changes': factors.change_size_score,
                    'issues': factors.issue_score,
                },
                recommendations=recommendations,
            )

            self.db.add(assessment)
            self.db.commit()

            return {
                'file_path': file_path,
                'overall_score': overall_score,
                'risk_category': risk_category,
                'factors': {
                    'complexity': factors.complexity_score,
                    'dependencies': factors.dependency_score,
                    'patterns': factors.pattern_complexity_score,
                    'changes': factors.change_size_score,
                    'issues': factors.issue_score,
                },
                'metrics': {
                    'lines_of_code': loc,
                    'nesting_depth': nesting,
                    'function_count': func_count,
                    'issue_count': issue_count,
                },
                'recommendations': recommendations,
            }
        except Exception as e:
            logger.error(f"Error assessing file risk: {e}")
            raise

    def get_job_risk_summary(self, job_id: str) -> Dict:
        """Get risk summary for entire job"""
        try:
            assessments = self.db.query(RiskAssessmentModel).filter_by(job_id=job_id).all()

            if not assessments:
                return {
                    'job_id': job_id,
                    'total_files': 0,
                    'critical_count': 0,
                    'high_count': 0,
                    'medium_count': 0,
                    'low_count': 0,
                    'average_score': 0.0,
                    'files': [],
                }

            critical = sum(1 for a in assessments if a.risk_category == 'CRITICAL')
            high = sum(1 for a in assessments if a.risk_category == 'HIGH')
            medium = sum(1 for a in assessments if a.risk_category == 'MEDIUM')
            low = sum(1 for a in assessments if a.risk_category == 'LOW')

            avg_score = sum(a.overall_score for a in assessments) / len(assessments)

            return {
                'job_id': job_id,
                'total_files': len(assessments),
                'critical_count': critical,
                'high_count': high,
                'medium_count': medium,
                'low_count': low,
                'average_score': avg_score,
                'files': [
                    {
                        'file_path': a.file_path,
                        'score': a.overall_score,
                        'category': a.risk_category,
                        'recommendations': a.recommendations,
                    }
                    for a in sorted(assessments, key=lambda x: x.overall_score, reverse=True)
                ],
            }
        except Exception as e:
            logger.error(f"Error getting risk summary: {e}")
            return {}

    def get_critical_files(self, job_id: str) -> List[Dict]:
        """Get files that need AI verification (HIGH/CRITICAL risk)"""
        try:
            assessments = self.db.query(RiskAssessmentModel).filter(
                (RiskAssessmentModel.job_id == job_id) &
                (RiskAssessmentModel.risk_category.in_(['HIGH', 'CRITICAL']))
            ).all()

            return [
                {
                    'file_path': a.file_path,
                    'score': a.overall_score,
                    'category': a.risk_category,
                }
                for a in assessments
            ]
        except Exception as e:
            logger.error(f"Error getting critical files: {e}")
            return []


# Global singleton
_risk_service: Optional[RiskAssessmentService] = None


def get_risk_assessment_service(db: Optional[Session] = None) -> RiskAssessmentService:
    """Get or create risk assessment service"""
    global _risk_service
    if _risk_service is None:
        _risk_service = RiskAssessmentService(db)
    return _risk_service
