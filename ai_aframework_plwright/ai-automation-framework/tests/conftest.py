"""
Root conftest for pytest - API TESTS ONLY
UI tests use Behave (see features/environment.py)
"""

import pytest
from typing import Dict
from utilities.logger import get_logger
from config.config import config

logger = get_logger(__name__)


def pytest_addoption(parser):
    """Add custom command line options for API tests"""
    parser.addoption(
        "--env",
        action="store",
        default=config.environment,
        help="Test environment: qa, staging, production"
    )


@pytest.fixture(scope="session")
def test_config(request) -> Dict:
    """Test configuration fixture for API tests"""
    return {
        'environment': request.config.getoption("--env"),
        'base_url': config.get_base_url(),
        'api_base_url': config.get_api_base_url(),
    }


@pytest.fixture(scope="session", autouse=True)
def setup_teardown_session():
    """Session-level setup and teardown"""
    logger.info("=" * 80)
    logger.info("TEST SESSION STARTED")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Base URL: {config.get_base_url()}")
    logger.info(f"Parallel Workers: {config.parallel_workers}")
    logger.info("=" * 80)

    yield

    logger.info("=" * 80)
    logger.info("TEST SESSION COMPLETED")
    logger.info("=" * 80)

    # Cleanup
    try:
        from core.driver_factory import DriverFactory
        DriverFactory.cleanup()
    except ImportError:
        pass  # DriverFactory not needed for API tests


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Make test result available in fixtures
    Used for capturing screenshots on failure
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def log_test_info(request):
    """Log test information"""
    logger.info("=" * 60)
    logger.info(f"Test: {request.node.name}")
    logger.info(f"Module: {request.node.module.__name__}")
    logger.info("=" * 60)