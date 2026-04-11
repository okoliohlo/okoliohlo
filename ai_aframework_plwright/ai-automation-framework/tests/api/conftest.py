"""
API tests conftest
Fixtures specific to API tests
"""

import pytest
from core.api_client import APIClient
from business.api.endpoints.auth_endpoint import AuthEndpoint
from business.api.endpoints.user_endpoint import UserEndpoint
from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="function")
def api_client() -> APIClient:
    """Create API client"""
    client = APIClient()
    yield client
    # Cleanup
    client.session.close()


@pytest.fixture(scope="function")
def auth_endpoint(api_client) -> AuthEndpoint:
    """Auth endpoint fixture"""
    return AuthEndpoint(api_client)


@pytest.fixture(scope="function")
def user_endpoint(api_client) -> UserEndpoint:
    """User endpoint fixture"""
    return UserEndpoint(api_client)


# @pytest.fixture(scope="function")
# def product_endpoint(api_client) -> ProductEndpoint:
#     """Product endpoint fixture"""
#     return ProductEndpoint(api_client)


@pytest.fixture(scope="function")
def authenticated_api_client(api_client, auth_endpoint) -> APIClient:
    """
    API client with authenticated session
    Logs in before test and returns client with token
    """
    credentials = config.get_credentials("standard")

    # Login via API
    response = auth_endpoint.login(
        credentials["username"],
        credentials["password"]
    )

    # Token is automatically set in api_client
    yield api_client

    # Logout
    try:
        auth_endpoint.logout()
    except Exception:
        pass