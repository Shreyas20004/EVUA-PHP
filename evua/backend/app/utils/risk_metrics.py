"""
Risk Assessment Metrics
Calculates risk scores based on code complexity, patterns, and migration factors
"""
import re
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger("evua.risk_metrics")


@dataclass
class RiskFactors:
    """Aggregated risk factors"""
    complexity_score: float  # 0-1
    dependency_score: float  # 0-1
    pattern_complexity_score: float  # 0-1
    issue_score: float  # 0-1
    change_size_score: float  # 0-1


class RiskMetricsCalculator:
    """Calculate risk metrics for PHP code migrations"""

    @staticmethod
    def measure_complexity(code: str) -> Tuple[int, int, int]:
        """
        Measure code complexity metrics.
        Returns: (lines_of_code, max_nesting_depth, function_count)
        """
        lines = code.split('\n')
        loc = len([l for l in lines if l.strip() and not l.strip().startswith('//')])

        # Count nesting depth
        max_depth = 0
        current_depth = 0
        for char in code:
            if char in '{(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in '})':
                current_depth -= 1

        # Count functions
        function_pattern = r'function\s+\w+\s*\('
        function_count = len(re.findall(function_pattern, code, re.IGNORECASE))

        return loc, max_depth, function_count

    @staticmethod
    def measure_dependencies(code: str) -> Dict[str, int]:
        """
        Measure external library and function dependencies.
        Returns dict of dependency counts
        """
        deps = {
            'mysql_': len(re.findall(r'mysql_\w+', code)),
            'curl_': len(re.findall(r'curl_\w+', code)),
            'preg_': len(re.findall(r'preg_\w+', code)),
            'file_': len(re.findall(r'file_\w+', code)),
            'json_': len(re.findall(r'json_\w+', code)),
            'pdo_': len(re.findall(r'pdo_\w+', code, re.IGNORECASE)),
            'fopen': len(re.findall(r'fopen\s*\(', code)),
            'eval': len(re.findall(r'eval\s*\(', code)),
            'global': len(re.findall(r'\bglobal\s+\$', code)),
        }
        return deps

    @staticmethod
    def measure_pattern_complexity(code: str, original_code: str) -> Dict[str, int]:
        """
        Measure complex patterns that might indicate risk.
        """
        patterns = {
            'dynamic_vars': len(re.findall(r'\$\$', code)),  # Variable variables
            'string_eval': len(re.findall(r'eval|create_function', code, re.IGNORECASE)),
            'magic_methods': len(re.findall(r'__\w+', code)),
            'regex_patterns': len(re.findall(r"preg_|ereg", code)),
            'type_juggling': len(re.findall(r'==|!=(?!=)', code)),  # Loose comparison
            'serialize': len(re.findall(r'serialize|unserialize', code, re.IGNORECASE)),
        }
        return patterns

    @staticmethod
    def calculate_change_size(original: str, migrated: str) -> float:
        """
        Calculate percentage of code that changed.
        Returns: 0.0 - 1.0 (0 = no change, 1 = completely different)
        """
        if not original:
            return 1.0

        orig_lines = set(original.split('\n'))
        mig_lines = set(migrated.split('\n'))

        if not orig_lines:
            return 0.0

        changed = len(orig_lines.symmetric_difference(mig_lines))
        return min(changed / len(orig_lines), 1.0)

    @staticmethod
    def calculate_scores(
        original_code: str,
        migrated_code: str,
        issue_count: int = 0,
        ai_confidence: float = 1.0,
    ) -> RiskFactors:
        """
        Calculate all risk factor scores.

        Args:
            original_code: Original PHP code
            migrated_code: Migrated PHP code
            issue_count: Number of issues found
            ai_confidence: AI's confidence in the migration (0-1)

        Returns:
            RiskFactors with normalized scores
        """
        # Complexity metrics
        loc, nesting, func_count = RiskMetricsCalculator.measure_complexity(migrated_code)

        # Normalize complexity (high values = high risk)
        complexity_score = min(1.0, (
            (loc / 1000) * 0.3 +  # LOC factor
            (nesting / 10) * 0.4 +  # Nesting depth factor
            (func_count / 50) * 0.3  # Function count factor
        ))

        # Dependency risk
        deps = RiskMetricsCalculator.measure_dependencies(migrated_code)
        total_deps = sum(deps.values())
        dependency_score = min(1.0, (
            (deps.get('mysql_', 0) / 5) * 0.3 +  # Old MySQL API = high risk
            (deps.get('eval', 0) / 2) * 0.4 +  # eval = very high risk
            (total_deps / 20) * 0.3  # Overall deps
        ))

        # Pattern complexity
        patterns = RiskMetricsCalculator.measure_pattern_complexity(migrated_code, original_code)
        total_patterns = sum(patterns.values())
        pattern_complexity_score = min(1.0, (
            (patterns.get('dynamic_vars', 0) / 5) * 0.2 +
            (patterns.get('string_eval', 0) * 0.3) +
            (patterns.get('magic_methods', 0) / 10) * 0.2 +
            (patterns.get('type_juggling', 0) / 20) * 0.2 +
            (patterns.get('serialize', 0) / 5) * 0.1
        ))

        # Issue-based score
        issue_score = min(1.0, issue_count / 10)

        # Change size score
        change_size_score = RiskMetricsCalculator.calculate_change_size(original_code, migrated_code)

        return RiskFactors(
            complexity_score=complexity_score,
            dependency_score=dependency_score,
            pattern_complexity_score=pattern_complexity_score,
            issue_score=issue_score,
            change_size_score=change_size_score,
        )

    @staticmethod
    def calculate_overall_risk(factors: RiskFactors, ai_confidence: float = 1.0) -> Tuple[float, str]:
        """
        Calculate overall risk score from individual factors.

        Returns:
            (risk_score: 0-1, category: LOW/MEDIUM/HIGH/CRITICAL)
        """
        # Weighted combination
        overall = (
            factors.complexity_score * 0.2 +
            factors.dependency_score * 0.25 +
            factors.pattern_complexity_score * 0.15 +
            (1.0 - ai_confidence) * 0.2 +  # Inverse: low AI confidence = high risk
            factors.change_size_score * 0.1 +
            factors.issue_score * 0.1
        )

        # Categorize
        if overall < 0.25:
            category = 'LOW'
        elif overall < 0.6:
            category = 'MEDIUM'
        elif overall < 0.8:
            category = 'HIGH'
        else:
            category = 'CRITICAL'

        return overall, category

    @staticmethod
    def get_risk_recommendations(factors: RiskFactors, risk_category: str) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []

        if factors.complexity_score > 0.7:
            recommendations.append('Complex code detected. Manual review recommended.')

        if factors.dependency_score > 0.7:
            recommendations.append('High dependency risk. Review external API calls.')

        if factors.pattern_complexity_score > 0.7:
            recommendations.append('Complex patterns found. May require expert review.')

        if factors.issue_score > 0.7:
            recommendations.append('Multiple issues detected. Address all issues before deployment.')

        if factors.change_size_score > 0.8:
            recommendations.append('Significant code changes. Recommend full testing.')

        if risk_category == 'CRITICAL':
            recommendations.append('CRITICAL RISK: AI verification recommended.')

        if not recommendations:
            recommendations.append('Code appears safe to deploy.')

        return recommendations
