"""
API Client Wrapper
Handles HTTP requests with logging, retries, and response validation
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
import json
from config.config import config
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class APIClient:
    """
    HTTP client for API testing with enhanced features
    """

    def __init__(self, base_url: str = None):
        """
        Initialize API client

        Args:
            base_url: Base URL for API (uses config if None)
        """
        self.base_url = base_url or config.get_api_base_url()
        self.session = self._create_session()
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self._auth_token = None

    def _create_session(self) -> requests.Session:
        """Create session with retry strategy"""
        session = requests.Session()

        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def set_auth_token(self, token: str):
        """Set authentication token"""
        self._auth_token = token
        self.headers["Authorization"] = f"Bearer {token}"
        logger.info("Authentication token set")

    def clear_auth_token(self):
        """Clear authentication token"""
        self._auth_token = None
        if "Authorization" in self.headers:
            del self.headers["Authorization"]
        logger.info("Authentication token cleared")

    @allure.step("API Request: {method} {endpoint}")
    def request(
            self,
            method: str,
            endpoint: str,
            params: Dict = None,
            data: Any = None,
            json_data: Dict = None,
            headers: Dict = None,
            **kwargs
    ) -> requests.Response:
        """
        Make HTTP request

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            json_data: JSON request body
            headers: Additional headers
            **kwargs: Additional request arguments

        Returns:
            Response object
        """
        url = f"{self.base_url}{endpoint}"

        # Merge headers
        request_headers = {**self.headers}
        if headers:
            request_headers.update(headers)

        # Log request
        logger.info(f"API Request: {method} {url}")
        logger.debug(f"Headers: {request_headers}")

        if params:
            logger.debug(f"Params: {params}")

        if json_data:
            logger.debug(f"JSON Body: {json.dumps(json_data, indent=2)}")

        # Make request
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                json=json_data,
                headers=request_headers,
                **kwargs
            )

            # Log response
            logger.info(f"API Response: {response.status_code}")
            logger.debug(f"Response Body: {response.text[:500]}")  # First 500 chars

            # Attach to Allure report
            self._attach_to_allure(method, url, request_headers, json_data, response)

            return response

        except Exception as e:
            logger.error(f"API Request failed: {str(e)}")
            raise

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        """GET request"""
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> requests.Response:
        """POST request"""
        return self.request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, **kwargs) -> requests.Response:
        """PUT request"""
        return self.request("PUT", endpoint, **kwargs)

    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        """PATCH request"""
        return self.request("PATCH", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        """DELETE request"""
        return self.request("DELETE", endpoint, **kwargs)

    def _attach_to_allure(
            self,
            method: str,
            url: str,
            headers: Dict,
            request_body: Any,
            response: requests.Response
    ):
        """Attach request/response details to Allure report"""
        # Request details
        request_data = {
            "method": method,
            "url": url,
            "headers": headers,
            "body": request_body
        }

        allure.attach(
            json.dumps(request_data, indent=2),
            name="Request",
            attachment_type=allure.attachment_type.JSON
        )

        # Response details
        response_data = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        }

        allure.attach(
            json.dumps(response_data, indent=2),
            name="Response",
            attachment_type=allure.attachment_type.JSON
        )

    def validate_status_code(self, response: requests.Response, expected: int):
        """
        Validate response status code

        Args:
            response: Response object
            expected: Expected status code

        Raises:
            AssertionError: If status code doesn't match
        """
        assert response.status_code == expected, \
            f"Expected status {expected}, got {response.status_code}. Response: {response.text}"

    def validate_response_time(self, response: requests.Response, max_time: float):
        """
        Validate response time

        Args:
            response: Response object
            max_time: Maximum acceptable time in seconds

        Raises:
            AssertionError: If response time exceeds maximum
        """
        elapsed = response.elapsed.total_seconds()
        assert elapsed <= max_time, \
            f"Response time {elapsed}s exceeded maximum {max_time}s"

    def validate_json_schema(self, response: requests.Response, schema: Dict):
        """
        Validate response against JSON schema

        Args:
            response: Response object
            schema: JSON schema dictionary

        Raises:
            ValidationError: If validation fails
        """
        from jsonschema import validate, ValidationError

        try:
            validate(instance=response.json(), schema=schema)
            logger.info("JSON schema validation passed")
        except ValidationError as e:
            logger.error(f"JSON schema validation failed: {str(e)}")
            raise