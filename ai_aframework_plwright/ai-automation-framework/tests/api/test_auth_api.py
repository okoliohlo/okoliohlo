"""
Authentication API Tests
"""

import pytest
import allure
from business.api.endpoints.auth_endpoint import AuthEndpoint
from business.api.schemas.user_schema import AUTH_RESPONSE_SCHEMA
from config.config import config


@allure.feature("Authentication API")
@allure.story("Login API")
@pytest.mark.api
@pytest.mark.smoke
class TestAuthAPI:
    """Authentication API test cases"""

    @allure.title("API: Successful login")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_api(self, auth_endpoint: AuthEndpoint):
        """Test successful login via API"""
        # Arrange
        credentials = config.get_credentials("standard")

        # Act
        response_data = auth_endpoint.login(
            credentials["username"],
            credentials["password"]
        )

        # Assert
        assert "token" in response_data, "Response should contain token"
        assert "user" in response_data, "Response should contain user data"
        assert response_data["user"]["username"] == credentials["username"]

        # Validate schema
        from jsonschema import validate
        validate(instance=response_data, schema=AUTH_RESPONSE_SCHEMA)

    @allure.title("API: Login with invalid credentials")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_login_invalid_credentials(self, auth_endpoint: AuthEndpoint, api_client):
        """Test login with invalid credentials"""
        # Arrange
        invalid_username = "invalid@test.com"
        invalid_password = "wrongpassword"

        # Act & Assert
        response = api_client.post(
            "/api/auth/login",
            json_data={
                "username": invalid_username,
                "password": invalid_password
            }
        )

        assert response.status_code in [401, 403], "Should return 401 or 403 for invalid credentials"

    @allure.title("API: Token verification")
    @allure.severity(allure.severity_level.NORMAL)
    def test_verify_token(self, authenticated_api_client, auth_endpoint: AuthEndpoint):
        """Test token verification"""
        # Act
        is_valid = auth_endpoint.verify_token()

        # Assert
        assert is_valid, "Token should be valid"

    @allure.title("API: Logout")
    @allure.severity(allure.severity_level.NORMAL)
    def test_logout(self, authenticated_api_client, auth_endpoint: AuthEndpoint):
        """Test logout"""
        # Act
        response_data = auth_endpoint.logout()

        # Assert
        assert "message" in response_data or "success" in response_data