"""
Base API Endpoint
Provides common methods for all API endpoints
"""

from core.api_client import APIClient
from typing import Dict, Any, Optional
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class BaseEndpoint:
    """Base class for API endpoints"""

    def __init__(self, api_client: APIClient = None):
        """
        Initialize base endpoint

        Args:
            api_client: API client instance
        """
        self.api_client = api_client or APIClient()
        self.base_path = ""

    @allure.step("Validate status code: {expected_status}")
    def validate_status_code(self, response, expected_status: int):
        """Validate response status code"""
        self.api_client.validate_status_code(response, expected_status)

    @allure.step("Validate response time <= {max_time}s")
    def validate_response_time(self, response, max_time: float):
        """Validate response time"""
        self.api_client.validate_response_time(response, max_time)

    @allure.step("Validate JSON schema")
    def validate_schema(self, response, schema: Dict):
        """Validate response against schema"""
        self.api_client.validate_json_schema(response, schema)

    def get_json_response(self, response) -> Dict:
        """
        Get JSON response

        Args:
            response: Response object

        Returns:
            JSON response as dictionary
        """
        try:
            return response.json()
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise

    def build_url(self, endpoint: str) -> str:
        """
        Build full URL

        Args:
            endpoint: Endpoint path

        Returns:
            Full URL
        """
        return f"{self.base_path}{endpoint}"