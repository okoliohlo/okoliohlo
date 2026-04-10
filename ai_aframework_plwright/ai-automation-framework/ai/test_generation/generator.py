"""
AI Test Generation Module
Generates test cases automatically from page objects and API endpoints
"""

import ast
import inspect
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
from utilities.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageElement:
    """Represents a page element"""
    name: str
    selector: str
    element_type: str  # input, button, link, etc.


@dataclass
class PageMethod:
    """Represents a page object method"""
    name: str
    params: List[str]
    doc: str


@dataclass
class GeneratedTest:
    """Represents a generated test"""
    name: str
    code: str
    description: str
    markers: List[str]


class AITestGenerator:
    """
    Generates test cases from page objects and API endpoints
    Uses AST parsing and pattern recognition
    """

    def __init__(self, project_root: Path = None):
        """
        Initialize test generator

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.business_dir = self.project_root / "business"
        self.tests_dir = self.project_root / "tests"
        
    def generate_ui_tests_from_page(self, page_class_path: str) -> List[GeneratedTest]:
        """
        Generate UI tests from a page object class

        Args:
            page_class_path: Path to page object file (e.g., "business/ui/pages/login_page.py")

        Returns:
            List of generated tests
        """
        logger.info(f"Generating tests from: {page_class_path}")
        
        file_path = self.project_root / page_class_path
        if not file_path.exists():
            raise FileNotFoundError(f"Page object not found: {file_path}")

        # Parse the page object
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)
        page_class = self._extract_page_class(tree)
        
        if not page_class:
            logger.warning(f"No page class found in {page_class_path}")
            return []

        # Extract elements and methods
        elements = self._extract_elements(page_class)
        methods = self._extract_methods(page_class)
        
        # Generate tests
        tests = []
        tests.extend(self._generate_element_visibility_tests(page_class['name'], elements))
        tests.extend(self._generate_interaction_tests(page_class['name'], methods))
        tests.extend(self._generate_workflow_tests(page_class['name'], methods))
        
        logger.info(f"Generated {len(tests)} tests for {page_class['name']}")
        return tests

    def generate_api_tests_from_endpoint(self, endpoint_class_path: str) -> List[GeneratedTest]:
        """
        Generate API tests from an endpoint class

        Args:
            endpoint_class_path: Path to endpoint file (e.g., "business/api/endpoints/user_endpoint.py")

        Returns:
            List of generated tests
        """
        logger.info(f"Generating API tests from: {endpoint_class_path}")
        
        file_path = self.project_root / endpoint_class_path
        if not file_path.exists():
            raise FileNotFoundError(f"Endpoint not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source)
        endpoint_class = self._extract_endpoint_class(tree)
        
        if not endpoint_class:
            logger.warning(f"No endpoint class found in {endpoint_class_path}")
            return []

        methods = self._extract_api_methods(endpoint_class)
        
        # Generate API tests
        tests = []
        for method in methods:
            tests.extend(self._generate_api_test_cases(endpoint_class['name'], method))
        
        logger.info(f"Generated {len(tests)} API tests for {endpoint_class['name']}")
        return tests

    def _extract_page_class(self, tree: ast.AST) -> Optional[Dict]:
        """Extract page class information from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a page class (inherits from BasePage)
                for base in node.bases:
                    if isinstance(base, ast.Name) and 'Page' in base.id:
                        return {
                            'name': node.name,
                            'node': node,
                            'doc': ast.get_docstring(node) or ""
                        }
        return None

    def _extract_endpoint_class(self, tree: ast.AST) -> Optional[Dict]:
        """Extract endpoint class information from AST"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if 'Endpoint' in node.name:
                    return {
                        'name': node.name,
                        'node': node,
                        'doc': ast.get_docstring(node) or ""
                    }
        return None

    def _extract_elements(self, page_class: Dict) -> List[PageElement]:
        """Extract page elements (locators) from page class"""
        elements = []
        node = page_class['node']
        
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Check if it's a locator (uppercase constant)
                        if var_name.isupper() and not var_name.endswith('_NAME'):
                            if isinstance(item.value, ast.Constant):
                                selector = item.value.value
                                element_type = self._infer_element_type(var_name, selector)
                                elements.append(PageElement(
                                    name=var_name,
                                    selector=selector,
                                    element_type=element_type
                                ))
        
        return elements

    def _extract_methods(self, page_class: Dict) -> List[PageMethod]:
        """Extract methods from page class"""
        methods = []
        node = page_class['node']
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                # Skip private and special methods
                if item.name.startswith('_'):
                    continue
                
                params = [arg.arg for arg in item.args.args if arg.arg != 'self']
                doc = ast.get_docstring(item) or ""
                
                methods.append(PageMethod(
                    name=item.name,
                    params=params,
                    doc=doc
                ))
        
        return methods

    def _extract_api_methods(self, endpoint_class: Dict) -> List[PageMethod]:
        """Extract API methods from endpoint class"""
        return self._extract_methods(endpoint_class)

    def _infer_element_type(self, name: str, selector: str) -> str:
        """Infer element type from name and selector"""
        name_lower = name.lower()
        selector_lower = selector.lower()
        
        if 'button' in name_lower or 'btn' in name_lower or 'button' in selector_lower:
            return 'button'
        elif 'input' in name_lower or 'field' in name_lower or 'input' in selector_lower:
            return 'input'
        elif 'link' in name_lower or 'a[' in selector_lower:
            return 'link'
        elif 'checkbox' in name_lower or 'checkbox' in selector_lower:
            return 'checkbox'
        elif 'dropdown' in name_lower or 'select' in selector_lower:
            return 'dropdown'
        else:
            return 'element'

    def _generate_element_visibility_tests(self, page_name: str, elements: List[PageElement]) -> List[GeneratedTest]:
        """Generate visibility tests for page elements"""
        tests = []
        
        if not elements:
            return tests

        page_var = self._to_snake_case(page_name)
        
        test_code = f'''"""
Test {page_name} element visibility
Auto-generated test
"""

import pytest
import allure
from business.ui.pages.{self._to_snake_case(page_name.replace("Page", "_page"))} import {page_name}


@allure.feature("{page_name.replace('Page', '')}")
@allure.story("Element Visibility")
@pytest.mark.ui
@pytest.mark.smoke
class Test{page_name}Visibility:
    """Test visibility of {page_name} elements"""

    @allure.title("Verify all critical elements are visible")
    def test_critical_elements_visible(self, {page_var}: {page_name}):
        """Test that all critical elements are visible on the page"""
        {page_var}.open()
        
'''
        
        for element in elements[:5]:  # Limit to first 5 elements
            element_name_readable = element.name.replace('_', ' ').title()
            test_code += f'        # Verify {element_name_readable}\n'
            test_code += f'        assert {page_var}.is_element_visible({page_var}.{element.name}), "{element_name_readable} should be visible"\n'
            test_code += '\n'

        tests.append(GeneratedTest(
            name=f"test_{self._to_snake_case(page_name)}_visibility",
            code=test_code,
            description=f"Visibility tests for {page_name}",
            markers=["ui", "smoke"]
        ))
        
        return tests

    def _generate_interaction_tests(self, page_name: str, methods: List[PageMethod]) -> List[GeneratedTest]:
        """Generate interaction tests for page methods"""
        tests = []
        page_var = self._to_snake_case(page_name)
        
        for method in methods:
            if method.name in ['open', '__init__']:
                continue
                
            test_name = f"test_{method.name}"
            method_title = method.name.replace('_', ' ').title()
            
            test_code = f'''"""
Test {page_name}.{method.name}() method
Auto-generated test
"""

import pytest
import allure
from business.ui.pages.{self._to_snake_case(page_name.replace("Page", "_page"))} import {page_name}


@allure.feature("{page_name.replace('Page', '')}")
@allure.story("{method_title}")
@pytest.mark.ui
class Test{page_name}{method.name.title().replace("_", "")}:
    """Test {method.name} functionality"""

    @allure.title("Test {method_title}")
    def {test_name}(self, {page_var}: {page_name}):
        """
        Test {method.name} method
        {method.doc}
        """
        {page_var}.open()
        
        # TODO: Add test implementation
        # Example: {page_var}.{method.name}({self._generate_sample_params(method.params)})
        
        pass  # Replace with actual test logic
'''
            
            tests.append(GeneratedTest(
                name=test_name,
                code=test_code,
                description=f"Test for {method.name} method",
                markers=["ui"]
            ))
        
        return tests[:3]  # Limit to 3 interaction tests

    def _generate_workflow_tests(self, page_name: str, methods: List[PageMethod]) -> List[GeneratedTest]:
        """Generate workflow/integration tests"""
        tests = []
        
        # Look for common workflows (login, checkout, etc.)
        workflow_methods = [m for m in methods if any(keyword in m.name.lower() 
                           for keyword in ['login', 'submit', 'checkout', 'complete'])]
        
        if not workflow_methods:
            return tests

        page_var = self._to_snake_case(page_name)
        workflow_name = workflow_methods[0].name
        
        test_code = f'''"""
Test {page_name} workflow
Auto-generated integration test
"""

import pytest
import allure
from business.ui.pages.{self._to_snake_case(page_name.replace("Page", "_page"))} import {page_name}


@allure.feature("{page_name.replace('Page', '')}")
@allure.story("Workflow")
@pytest.mark.ui
@pytest.mark.integration
class Test{page_name}Workflow:
    """Test complete workflow for {page_name}"""

    @allure.title("Test complete {workflow_name} workflow")
    def test_{workflow_name}_workflow(self, {page_var}: {page_name}):
        """Test end-to-end {workflow_name} workflow"""
        {page_var}.open()
        
        # TODO: Implement complete workflow
        # Step 1: Navigate to page
        # Step 2: Fill required fields
        # Step 3: Submit/Complete action
        # Step 4: Verify success
        
        pass  # Replace with actual workflow
'''
        
        tests.append(GeneratedTest(
            name=f"test_{workflow_name}_workflow",
            code=test_code,
            description=f"Workflow test for {page_name}",
            markers=["ui", "integration"]
        ))
        
        return tests

    def _generate_api_test_cases(self, endpoint_name: str, method: PageMethod) -> List[GeneratedTest]:
        """Generate API test cases for an endpoint method"""
        tests = []
        endpoint_var = self._to_snake_case(endpoint_name)
        http_method = self._infer_http_method(method.name)
        
        # Generate success test
        test_code = f'''"""
Test {endpoint_name}.{method.name}() API endpoint
Auto-generated test
"""

import pytest
import allure
from business.api.endpoints.{self._to_snake_case(endpoint_name.replace("Endpoint", "_endpoint"))} import {endpoint_name}


@allure.feature("{endpoint_name.replace('Endpoint', '')} API")
@allure.story("{method.name.title()}")
@pytest.mark.api
class Test{endpoint_name}{method.name.title().replace("_", "")}:
    """Test {method.name} API endpoint"""

    @allure.title("Test {method.name} - Success")
    def test_{method.name}_success(self, {endpoint_var}: {endpoint_name}):
        """Test successful {method.name} request"""
        # Arrange
        # TODO: Prepare test data
        
        # Act
        response = {endpoint_var}.{method.name}({self._generate_sample_params(method.params)})
        
        # Assert
        assert response.status_code == 200, "Should return 200 OK"
        # TODO: Add more assertions
        
    @allure.title("Test {method.name} - Invalid Data")
    def test_{method.name}_invalid_data(self, {endpoint_var}: {endpoint_name}):
        """Test {method.name} with invalid data"""
        # Arrange
        # TODO: Prepare invalid test data
        
        # Act & Assert
        # TODO: Test error handling
        pass
'''
        
        tests.append(GeneratedTest(
            name=f"test_{method.name}_api",
            code=test_code,
            description=f"API tests for {method.name}",
            markers=["api"]
        ))
        
        return tests

    def _infer_http_method(self, method_name: str) -> str:
        """Infer HTTP method from method name"""
        name_lower = method_name.lower()
        if name_lower.startswith('get') or name_lower.startswith('fetch'):
            return 'GET'
        elif name_lower.startswith('create') or name_lower.startswith('add'):
            return 'POST'
        elif name_lower.startswith('update') or name_lower.startswith('edit'):
            return 'PUT'
        elif name_lower.startswith('delete') or name_lower.startswith('remove'):
            return 'DELETE'
        return 'GET'

    def _generate_sample_params(self, params: List[str]) -> str:
        """Generate sample parameters for method calls"""
        if not params:
            return ""
        
        sample_values = []
        for param in params:
            param_lower = param.lower()
            if 'id' in param_lower:
                sample_values.append('1')
            elif 'name' in param_lower or 'username' in param_lower:
                sample_values.append('"test_user"')
            elif 'email' in param_lower:
                sample_values.append('"test@example.com"')
            elif 'password' in param_lower:
                sample_values.append('"Test@123"')
            elif 'data' in param_lower:
                sample_values.append('{}')
            else:
                sample_values.append('"test_value"')
        
        return ', '.join(sample_values)

    def _to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case"""
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        return name.lower()

    def save_tests(self, tests: List[GeneratedTest], output_dir: Path):
        """
        Save generated tests to files

        Args:
            tests: List of generated tests
            output_dir: Output directory for test files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for test in tests:
            file_name = f"{test.name}.py"
            file_path = output_dir / file_name
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(test.code)
            
            logger.info(f"Saved test: {file_path}")

    def generate_all_ui_tests(self) -> Dict[str, List[GeneratedTest]]:
        """Generate tests for all UI page objects"""
        pages_dir = self.business_dir / "ui" / "pages"
        all_tests = {}
        
        for page_file in pages_dir.glob("*_page.py"):
            if page_file.name == "base_page.py":
                continue
            
            relative_path = page_file.relative_to(self.project_root)
            try:
                tests = self.generate_ui_tests_from_page(str(relative_path))
                all_tests[page_file.stem] = tests
            except Exception as e:
                logger.error(f"Failed to generate tests for {page_file}: {e}")
        
        return all_tests

    def generate_all_api_tests(self) -> Dict[str, List[GeneratedTest]]:
        """Generate tests for all API endpoints"""
        endpoints_dir = self.business_dir / "api" / "endpoints"
        all_tests = {}
        
        for endpoint_file in endpoints_dir.glob("*_endpoint.py"):
            if endpoint_file.name == "base_endpoint.py":
                continue
            
            relative_path = endpoint_file.relative_to(self.project_root)
            try:
                tests = self.generate_api_tests_from_endpoint(str(relative_path))
                all_tests[endpoint_file.stem] = tests
            except Exception as e:
                logger.error(f"Failed to generate tests for {endpoint_file}: {e}")
        
        return all_tests


def main():
    """CLI entry point for test generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Test Generator")
    parser.add_argument("--type", choices=["ui", "api", "all"], default="all",
                       help="Type of tests to generate")
    parser.add_argument("--page", help="Specific page object to generate tests for")
    parser.add_argument("--endpoint", help="Specific API endpoint to generate tests for")
    parser.add_argument("--output", help="Output directory for generated tests")
    
    args = parser.parse_args()
    
    generator = AITestGenerator()
    
    if args.page:
        tests = generator.generate_ui_tests_from_page(args.page)
        output_dir = Path(args.output) if args.output else generator.tests_dir / "generated" / "ui"
        generator.save_tests(tests, output_dir)
        print(f"✅ Generated {len(tests)} UI tests")
        
    elif args.endpoint:
        tests = generator.generate_api_tests_from_endpoint(args.endpoint)
        output_dir = Path(args.output) if args.output else generator.tests_dir / "generated" / "api"
        generator.save_tests(tests, output_dir)
        print(f"✅ Generated {len(tests)} API tests")
        
    elif args.type == "ui" or args.type == "all":
        all_tests = generator.generate_all_ui_tests()
        total = sum(len(tests) for tests in all_tests.values())
        output_dir = Path(args.output) if args.output else generator.tests_dir / "generated" / "ui"
        
        for page_name, tests in all_tests.items():
            generator.save_tests(tests, output_dir / page_name)
        
        print(f"✅ Generated {total} UI tests for {len(all_tests)} pages")
    
    if args.type == "api" or args.type == "all":
        all_tests = generator.generate_all_api_tests()
        total = sum(len(tests) for tests in all_tests.values())
        output_dir = Path(args.output) if args.output else generator.tests_dir / "generated" / "api"
        
        for endpoint_name, tests in all_tests.items():
            generator.save_tests(tests, output_dir / endpoint_name)
        
        print(f"✅ Generated {total} API tests for {len(all_tests)} endpoints")


if __name__ == "__main__":
    main()
