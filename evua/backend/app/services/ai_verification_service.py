"""
AI Verification Service
Routes high-risk code to AI for additional validation and correction
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session
import asyncio
import uuid

logger = logging.getLogger("evua.ai_verification_service")

# Add engine to path
# Walk up from this file until we find the directory containing engine/
_srv = Path(__file__).resolve()
_project_root = next(
    (p for p in _srv.parents if (p / "engine").is_dir()),
    _srv.parents[2],
)
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from engine.ai_processor import GeminiProcessor, MockAIProcessor
from ..db import SessionLocal, AIVerificationModel


class AIVerificationService:
    """
    Verifies high-risk code through AI processing.
    Automatically triggered after risk assessment.
    """

    def __init__(self, db: Optional[Session] = None, gemini_api_key: Optional[str] = None):
        self.db = db or SessionLocal()
        self.use_mock = not gemini_api_key
        self.ai_processor = (
            MockAIProcessor() if self.use_mock
            else GeminiProcessor(api_key=gemini_api_key)
        )

    async def verify_file(
        self,
        job_id: str,
        file_path: str,
        original_code: str,
        migrated_code: str,
        risk_factors: Optional[Dict] = None,
        auto_apply: bool = False,
    ) -> Dict:
        """
        Verify high-risk code through AI.

        Args:
            job_id: Migration job ID
            file_path: File path
            original_code: Original PHP code
            migrated_code: Migrated PHP code
            risk_factors: Dict of risk metrics
            auto_apply: Auto-apply if confidence > 0.8

        Returns:
            Verification result with feedback and suggestions
        """
        try:
            section_id = str(uuid.uuid4())[:12]

            # Prepare AI prompt with risk context
            prompt = self._build_verification_prompt(
                original_code,
                migrated_code,
                risk_factors,
            )

            # Get AI feedback
            logger.info(f"Sending file {file_path} to AI for verification")
            ai_response = await self._call_ai_processor(prompt)

            # Parse AI response
            suggestion, confidence, issues_found = self._parse_ai_response(ai_response)

            # Store verification record
            verification = AIVerificationModel(
                job_id=job_id,
                file_path=file_path,
                section_id=section_id,
                original_code=original_code,
                migrated_code=migrated_code,
                review_status='reviewed',
                ai_feedback=ai_response,
                suggested_fix=suggestion,
                confidence_score=confidence,
                issues_found=issues_found,
                fix_applied=False,
            )

            self.db.add(verification)
            self.db.commit()

            logger.info(f"Verification recorded for {file_path} (confidence: {confidence})")

            return {
                'section_id': section_id,
                'file_path': file_path,
                'status': 'reviewed',
                'ai_feedback': ai_response,
                'suggested_fix': suggestion,
                'confidence': confidence,
                'issues_found': issues_found,
                'auto_applied': False,
                'review_timestamp': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error verifying file: {e}")
            raise

    def get_verifications(self, job_id: str) -> List[Dict]:
        """Get all AI verifications for a job"""
        try:
            verifications = self.db.query(AIVerificationModel).filter_by(job_id=job_id).all()

            return [
                {
                    'section_id': v.section_id,
                    'file_path': v.file_path,
                    'status': v.review_status,
                    'confidence': v.confidence_score,
                    'ai_feedback': v.ai_feedback,
                    'suggested_fix': v.suggested_fix,
                    'approved': v.approved_by_user,
                    'fix_applied': v.fix_applied,
                }
                for v in verifications
            ]
        except Exception as e:
            logger.error(f"Error getting verifications: {e}")
            return []

    def approve_suggestion(self, section_id: str, reviewer_notes: Optional[str] = None) -> bool:
        """Approve an AI suggestion"""
        try:
            verification = self.db.query(AIVerificationModel).filter_by(
                section_id=section_id
            ).first()

            if not verification:
                return False

            verification.approved_by_user = True
            verification.reviewer_notes = reviewer_notes
            verification.reviewed_at = datetime.utcnow()
            verification.review_status = 'accepted'

            self.db.commit()
            logger.info(f"Suggestion {section_id} approved by user")
            return True
        except Exception as e:
            logger.error(f"Error approving suggestion: {e}")
            return False

    def reject_suggestion(self, section_id: str, reason: Optional[str] = None) -> bool:
        """Reject an AI suggestion"""
        try:
            verification = self.db.query(AIVerificationModel).filter_by(
                section_id=section_id
            ).first()

            if not verification:
                return False

            verification.approved_by_user = False
            verification.reviewer_notes = reason or "Rejected by user"
            verification.reviewed_at = datetime.utcnow()
            verification.review_status = 'rejected'

            self.db.commit()
            logger.info(f"Suggestion {section_id} rejected by user")
            return True
        except Exception as e:
            logger.error(f"Error rejecting suggestion: {e}")
            return False

    def apply_fix(self, section_id: str) -> Optional[str]:
        """Apply an AI suggestion and return the corrected code"""
        try:
            verification = self.db.query(AIVerificationModel).filter_by(
                section_id=section_id
            ).first()

            if not verification or not verification.suggested_fix:
                return None

            verification.fix_applied = True
            verification.fix_applied_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"Fix applied for section {section_id}")
            return verification.suggested_fix
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return None

    # -----------------------------------------------------------------------
    # Private methods
    # -----------------------------------------------------------------------

    def _build_verification_prompt(
        self,
        original_code: str,
        migrated_code: str,
        risk_factors: Optional[Dict] = None,
    ) -> str:
        """Build AI verification prompt"""
        prompt = f"""Review this PHP code migration for potential issues:

ORIGINAL CODE (PHP 5.6-7.4):
```php
{original_code}
```

MIGRATED CODE (PHP 8.0+):
```php
{migrated_code}
```

Please analyze for:
1. **Runtime Errors**: Code that will fail during execution
2. **Logic Bugs**: Functionality that changed unexpectedly
3. **Performance Issues**: Code that runs slower
4. **Security Vulnerabilities**: New security risks introduced
5. **Type Errors**: PHP 8 strict type violations
6. **Compatibility Issues**: Functions/features no longer available

---

RISK ASSESSMENT CONTEXT:
{self._format_risk_factors(risk_factors)}

---

REQUIRED RESPONSE:
Provide your analysis in JSON format:
{{
    "issues": [
        {{"severity": "critical|high|medium|low", "description": "...", "line": 1}},
        ...
    ],
    "suggested_fix": "corrected code here",
    "confidence": 0.85,
    "summary": "brief summary of changes"
}}
"""
        return prompt

    def _format_risk_factors(self, risk_factors: Optional[Dict]) -> str:
        """Format risk factors for AI context"""
        if not risk_factors:
            return "No specific risk factors provided"

        lines = ["Risk Factors:"]
        for key, value in risk_factors.items():
            if isinstance(value, float):
                lines.append(f"  - {key}: {value:.2f}")
            else:
                lines.append(f"  - {key}: {value}")
        return "\n".join(lines)

    async def _call_ai_processor(self, prompt: str) -> str:
        """Call AI processor with prompt"""
        try:
            if hasattr(self.ai_processor, 'process_async'):
                return await self.ai_processor.process_async(prompt)
            else:
                # Fallback to sync call wrapped in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None,
                    self.ai_processor.process,
                    prompt,
                )
        except Exception as e:
            logger.error(f"Error calling AI processor: {e}")
            raise

    def _parse_ai_response(self, response: str) -> tuple:
        """Parse AI response to extract feedback, suggestion, and confidence"""
        try:
            import json

            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                suggestion = data.get('suggested_fix', '')
                confidence = data.get('confidence', 0.5)
                issues = data.get('issues', [])

                return suggestion, confidence, issues
        except Exception as e:
            logger.warning(f"Error parsing AI response: {e}")

        # Fallback
        return "", 0.5, [{"severity": "unknown", "description": response}]


# Global singleton
_ai_verify_service: Optional[AIVerificationService] = None


def get_ai_verification_service(
    db: Optional[Session] = None,
    gemini_api_key: Optional[str] = None,
) -> AIVerificationService:
    """Get or create AI verification service"""
    global _ai_verify_service
    if _ai_verify_service is None:
        _ai_verify_service = AIVerificationService(db, gemini_api_key)
    return _ai_verify_service
