"""
User API Endpoints
"""

from business.api.endpoints.base_endpoint import BaseEndpoint
from typing import Dict, List
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class UserEndpoint(BaseEndpoint):
    """User API endpoints"""

    def __init__(self, api_client=None):
        super().__init__(api_client)
        self.base_path = "/api/users"

    @allure.step("API: Get user by ID: {user_id}")
    def get_user(self, user_id: int) -> Dict:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User data
        """
        logger.info(f"API Get User: {user_id}")

        response = self.api_client.get(self.build_url(f"/{user_id}"))

        self.validate_status_code(response, 200)

        return self.get_json_response(response)

    @allure.step("API: Get all users")
    def get_all_users(self, page: int = 1, limit: int = 10) -> Dict:
        """
        Get all users with pagination

        Args:
            page: Page number
            limit: Items per page

        Returns:
            Users list and pagination info
        """
        logger.info(f"API Get All Users: page={page}, limit={limit}")

        params = {
            "page": page,
            "limit": limit
        }

        response = self.api_client.get(
            self.build_url(""),
            params=params
        )

        self.validate_status_code(response, 200)

        return self.get_json_response(response)

    @allure.step("API: Create user")
    def create_user(self, user_data: Dict) -> Dict:
        """
        Create new user

        Args:
            user_data: User data dictionary

        Returns:
            Created user data
        """
        logger.info(f"API Create User: {user_data.get('username')}")

        response = self.api_client.post(
            self.build_url(""),
            json_data=user_data
        )

        self.validate_status_code(response, 201)

        return self.get_json_response(response)

    @allure.step("API: Update user: {user_id}")
    def update_user(self, user_id: int, user_data: Dict) -> Dict:
        """
        Update user

        Args:
            user_id: User ID
            user_data: Updated user data

        Returns:
            Updated user data
        """
        logger.info(f"API Update User: {user_id}")

        response = self.api_client.put(
            self.build_url(f"/{user_id}"),
            json_data=user_data
        )

        self.validate_status_code(response, 200)

        return self.get_json_response(response)

    @allure.step("API: Delete user: {user_id}")
    def delete_user(self, user_id: int) -> Dict:
        """
        Delete user

        Args:
            user_id: User ID

        Returns:
            Response data
        """
        logger.info(f"API Delete User: {user_id}")

        response = self.api_client.delete(self.build_url(f"/{user_id}"))

        self.validate_status_code(response, 200)

        return self.get_json_response(response)

    @allure.step("API: Search users")
    def search_users(self, query: str) -> List[Dict]:
        """
        Search users

        Args:
            query: Search query

        Returns:
            List of matching users
        """
        logger.info(f"API Search Users: {query}")

        params = {"q": query}

        response = self.api_client.get(
            self.build_url("/search"),
            params=params
        )

        self.validate_status_code(response, 200)

        return self.get_json_response(response).get("users", [])