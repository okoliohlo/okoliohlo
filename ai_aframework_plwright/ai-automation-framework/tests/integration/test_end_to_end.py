"""
End-to-End Integration Tests
Tests combining UI and API
"""

import pytest
import allure
from core.base_test import IntegrationTest
from business.ui.flows.auth_flow import AuthFlow
from business.api.endpoints.product_endpoint import ProductEndpoint
from utilities.data_generator import TestDataGenerator


@allure.feature("Integration")
@allure.story("End-to-End Flow")
@pytest.mark.integration
@pytest.mark.e2e
class TestE2E(IntegrationTest):
    """End-to-end integration tests"""

    @allure.title("E2E: Create product via API and verify in UI")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_product_and_verify_ui(self, request):
        """Test creating product via API and verifying in UI"""
        # Setup
        self.setup_teardown(request)

        # Step 1: Create product via API
        product_data = TestDataGenerator.generate_product()
        product_endpoint = ProductEndpoint(self.api_client)

        with allure.step("Create product via API"):
            created_product = product_endpoint.create_product(product_data)
            product_name = created_product["name"]

        # Step 2: Login to UI
        auth_flow = AuthFlow(self.page)

        with allure.step("Login to application"):
            success = auth_flow.login_as_standard_user()
            assert success, "Login should be successful"

        # Step 3: Search for product in UI
        from business.ui.pages.landing_page import LandingPage
        landing = LandingPage(self.page)

        with allure.step(f"Search for product: {product_name}"):
            landing.search(product_name)
            product_count = landing.get_product_count()

        # Assert
        assert product_count > 0, f"Product '{product_name}' should be found in UI"