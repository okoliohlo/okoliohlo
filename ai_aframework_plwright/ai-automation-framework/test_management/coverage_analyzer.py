"""
Test Coverage Analyzer
Analyzes test coverage and scope
"""

import ast
from pathlib import Path
from typing import Dict, List, Set
from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


class CoverageAnalyzer:
    """Analyzes test coverage"""

    def __init__(self):
        self.project_root = config.project_root
        self.tests_dir = self.project_root / "tests"
        self.business_dir = self.project_root / "business"

    def analyze_test_coverage(self) -> Dict:
        """
        Analyze test coverage

        Returns:
            Coverage statistics
        """
        logger.info("Analyzing test coverage...")

        # Find all test files
        test_files = self._find_test_files()

        # Extract test functions
        test_functions = self._extract_test_functions(test_files)

        # Find page objects and endpoints
        page_objects = self._find_page_objects()
        api_endpoints = self._find_api_endpoints()

        # Analyze coverage
        coverage_data = {
            'total_test_files': len(test_files),
            'total_test_functions': len(test_functions),
            'ui_tests': len([t for t in test_functions if 'ui' in t.lower()]),
            'api_tests': len([t for t in test_functions if 'api' in t.lower()]),
            'integration_tests': len([t for t in test_functions if 'integration' in t.lower() or 'e2e' in t.lower()]),
            'page_objects_count': len(page_objects),
            'api_endpoints_count': len(api_endpoints),
            'test_files': [str(f.relative_to(self.project_root)) for f in test_files],
            'page_objects': page_objects,
            'api_endpoints': api_endpoints,
        }

        logger.info(f"Coverage analysis complete: {coverage_data['total_test_functions']} tests found")

        return coverage_data

    def _find_test_files(self) -> List[Path]:
        """Find all test files"""
        return list(self.tests_dir.rglob("test_*.py"))

    def _extract_test_functions(self, test_files: List[Path]) -> List[str]:
        """Extract test function names from files"""
        test_functions = []

        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                        test_functions.append(f"{test_file.stem}.{node.name}")

            except Exception as e:
                logger.warning(f"Failed to parse {test_file}: {str(e)}")

        return test_functions

    def _find_page_objects(self) -> List[str]:
        """Find all page object classes"""
        page_objects = []
        pages_dir = self.business_dir / "ui" / "pages"

        if not pages_dir.exists():
            return page_objects

        for page_file in pages_dir.glob("*.py"):
            if page_file.name == "__init__.py":
                continue

            try:
                with open(page_file, 'r') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        page_objects.append(f"{page_file.stem}.{node.name}")

            except Exception as e:
                logger.warning(f"Failed to parse {page_file}: {str(e)}")

        return page_objects

    def _find_api_endpoints(self) -> List[str]:
        """Find all API endpoint classes"""
        endpoints = []
        endpoints_dir = self.business_dir / "api" / "endpoints"

        if not endpoints_dir.exists():
            return endpoints

        for endpoint_file in endpoints_dir.glob("*.py"):
            if endpoint_file.name == "__init__.py":
                continue

            try:
                with open(endpoint_file, 'r') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        endpoints.append(f"{endpoint_file.stem}.{node.name}")

            except Exception as e:
                logger.warning(f"Failed to parse {endpoint_file}: {str(e)}")

        return endpoints

    def generate_coverage_report(self) -> str:
        """Generate coverage report"""
        coverage_data = self.analyze_test_coverage()

        report = f"""
Test Coverage Report
====================

Test Statistics:
- Total Test Files: {coverage_data['total_test_files']}
- Total Test Functions: {coverage_data['total_test_functions']}
- UI Tests: {coverage_data['ui_tests']}
- API Tests: {coverage_data['api_tests']}
- Integration Tests: {coverage_data['integration_tests']}

Page Objects:
- Total Page Objects: {coverage_data['page_objects_count']}

API Endpoints:
- Total API Endpoints: {coverage_data['api_endpoints_count']}
        """.strip()

        return report