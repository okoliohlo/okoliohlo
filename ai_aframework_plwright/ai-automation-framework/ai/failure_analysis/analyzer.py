"""
Failure Analysis Module
Analyzes test failures and identifies patterns
"""

from typing import Dict, List
import re
from collections import defaultdict
from utilities.logger import get_logger

logger = get_logger(__name__)


class FailureAnalyzer:
    """Analyzes test failures"""

    def __init__(self):
        self.failure_categories = {
            'timeout': r'timeout|timed out|time limit',
            'element_not_found': r'element not found|no such element|nosuchelement',
            'stale_element': r'stale element|element is stale',
            'assertion': r'assert|assertion error|expected',
            'network': r'network|connection|refused|reset',
            'api_error': r'status code [45]\d{2}|api error',
            'permission': r'permission denied|access denied|forbidden',
            'null_pointer': r'null|none type|cannot read property',
        }

    def analyze_failure(self, error_message: str, stack_trace: str) -> Dict:
        """
        Analyze test failure

        Args:
            error_message: Error message
            stack_trace: Stack trace

        Returns:
            Analysis result dictionary
        """
        combined_text = f"{error_message} {stack_trace}".lower()

        # Categorize failure
        category = self._categorize_failure(combined_text)

        # Extract key information
        analysis = {
            'category': category,
            'error_message': error_message,
            'root_cause': self._infer_root_cause(category, combined_text),
            'recommendation': self._get_recommendation(category),
            'priority': self._get_priority(category),
            'is_flaky': self._is_likely_flaky(category),
        }

        logger.info(f"Failure analyzed: {category}")

        return analysis

    def _categorize_failure(self, text: str) -> str:
        """Categorize failure based on error text"""
        for category, pattern in self.failure_categories.items():
            if re.search(pattern, text, re.IGNORECASE):
                return category

        return 'unknown'

    def _infer_root_cause(self, category: str, text: str) -> str:
        """Infer root cause based on category"""
        causes = {
            'timeout': 'Application performance degradation or network latency',
            'element_not_found': 'UI changes or incorrect locator',
            'stale_element': 'DOM manipulation timing issues',
            'assertion': 'Unexpected application behavior or test logic error',
            'network': 'Network connectivity or service availability issues',
            'api_error': 'Backend service error or invalid request',
            'permission': 'Authentication or authorization failure',
            'null_pointer': 'Missing data or uninitialized object',
        }

        return causes.get(category, 'Requires investigation')

    def _get_recommendation(self, category: str) -> str:
        """Get recommendation based on category"""
        recommendations = {
            'timeout': 'Check application performance, increase timeout if justified',
            'element_not_found': 'Enable self-healing, verify locators, check for UI changes',
            'stale_element': 'Implement proper wait strategies, refetch elements before interaction',
            'assertion': 'Review test expectations and application behavior',
            'network': 'Check network connectivity, verify service availability',
            'api_error': 'Investigate backend logs, verify API endpoint',
            'permission': 'Verify credentials, check user permissions',
            'null_pointer': 'Add null checks, verify data setup',
        }

        return recommendations.get(category, 'Perform detailed investigation')

    def _get_priority(self, category: str) -> str:
        """Determine failure priority"""
        high_priority = ['api_error', 'permission', 'assertion']
        medium_priority = ['element_not_found', 'network']

        if category in high_priority:
            return 'HIGH'
        elif category in medium_priority:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _is_likely_flaky(self, category: str) -> bool:
        """Check if failure is likely flaky"""
        flaky_categories = ['timeout', 'stale_element', 'network']
        return category in flaky_categories

    def analyze_multiple_failures(self, failures: List[Dict]) -> Dict:
        """
        Analyze multiple failures to find patterns

        Args:
            failures: List of failure dictionaries

        Returns:
            Pattern analysis
        """
        categories = defaultdict(list)

        for failure in failures:
            analysis = self.analyze_failure(
                failure.get('error_message', ''),
                failure.get('stack_trace', '')
            )
            categories[analysis['category']].append(failure)

        # Find most common category
        most_common = max(categories.items(), key=lambda x: len(x[1])) if categories else (None, [])

        return {
            'total_failures': len(failures),
            'categories': dict(categories),
            'most_common_category': most_common[0],
            'most_common_count': len(most_common[1]),
            'requires_immediate_attention': self._requires_immediate_attention(categories),
        }

    def _requires_immediate_attention(self, categories: Dict) -> bool:
        """Check if failures require immediate attention"""
        critical_categories = ['api_error', 'permission', 'assertion']

        for category in critical_categories:
            if len(categories.get(category, [])) >= 3:
                return True

        return False