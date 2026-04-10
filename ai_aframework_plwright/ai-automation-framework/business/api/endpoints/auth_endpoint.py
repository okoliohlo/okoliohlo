"""
Authentication API Endpoints
"""

from business.api.endpoints.base_endpoint import BaseEndpoint
from typing import Dict
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class AuthEndpoint(BaseEndpoint):
    """Authentication API endpoints"""

    def __init__(self, api_client=None):
        super().__init__(api_client)
        self.base_path = "/api/auth"

    @allure.step("API: Login with username: {username}")
    def login(self, username: str, password: str) -> Dict:
        """
        Login via API

        Args:
            username: Username
            password: Password

        Returns:
            Response JSON
        """
        logger.info(f"API Login: {username}")

        payload = {
            "username": username,
            "password": password
        }

        response = self.api_client.post(
            self.build_url("/login"),
            json_data=payload
        )

        self.validate_status_code(response, 200)
        self.validate_response_time(response, 2.0)

        json_response = self.get_json_response(response)

        # Store token if present
        if "token" in json_response:
            self.api_client.set_auth_token(json_response["token"])

        return json_response

    @allure.step("API: Logout")
    def logout(self) -> Dict:
        """
        Logout via API

        Returns:
            Response JSON
        """
        logger.info("API Logout")

        response = self.api_client.post(self.build_url("/logout"))

        self.validate_status_code(response, 200)

        # Clear token
        self.api_client.clear_auth_token()

        return self.get_json_response(response)

    @allure.step("API: Register user")
    def register(self, username: str, email: str, password: str) -> Dict:
        """
        Register new user

        Args:
            username: Username
            email: Email
            password: Password

        Returns:
            Response JSON
        """
        logger.info(f"API Register: {username}")

        payload = {
            "username": username,
            "email": email,
            "password": password
        }

        response = self.api_client.post(
            self.build_url("/register"),
            json_data=payload
        )

        self.validate_status_code(response, 201)

        return self.get_json_response(response)

    @allure.step("API: Refresh token")
    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh authentication token

        Args:
            refresh_token: Refresh token

        Returns:
            Response JSON
        """
        logger.info("API Refresh Token")

        payload = {
            "refresh_token": refresh_token
        }

        response = self.api_client.post(
            self.build_url("/refresh"),
            json_data=payload
        )

        self.validate_status_code(response, 200)

        json_response = self.get_json_response(response)

        # Update token
        if "token" in json_response:
            self.api_client.set_auth_token(json_response["token"])

        return json_response

    @allure.step("API: Verify token")
    def verify_token(self) -> bool:
        """
        Verify authentication token

        Returns:
            True if valid, False otherwise
        """
        logger.info("API Verify Token")

        response = self.api_client.get(self.build_url("/verify"))

        return response.status_code == 200