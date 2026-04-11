"""
Base Test Class
Provides common setup/teardown and utilities for all tests
"""

import pytest
import allure
from playwright.sync_api import Page, BrowserContext
from typing import Optional
from core.driver_factory import DriverFactory
from core.api_client import APIClient
from config.config import config
from utilities.logger import get_logger
from utilities.screenshot_manager import ScreenshotManager
from datetime import datetime

logger = get_logger(__name__)


class BaseTest:
    """
    Base class for all test classes
    Provides common fixtures and utilities
    """

    # Class-level instances
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None
    api_client: Optional[APIClient] = None

    @pytest.fixture(scope="function", autouse=True)
    def setup_teardown(self, request):
        """
        Setup and teardown for each test

        Args:
            request: Pytest request fixture
        """
        test_name = request.node.name
        logger.info(f"Starting test: {test_name}")

        # Setup
        self._setup()

        yield

        # Teardown
        self._teardown(request)

        logger.info(f"Finished test: {test_name}")

    def _setup(self):
        """Setup method - override in subclasses if needed"""
        pass

    def _teardown(self, request):
        """Teardown method with screenshot on failure"""
        # Capture screenshot on failure
        if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
            self.capture_screenshot(request.node.name)

        # Close page and context
        if self.page:
            try:
                # Save video if enabled
                if config.video_recording != "off" and self.context:
                    video_path = self.page.video.path()
                    logger.info(f"Video saved: {video_path}")
            except Exception:
                pass

        if self.context:
            self.context.close()
            self.context = None

        self.page = None

    def capture_screenshot(self, name: str):
        """
        Capture screenshot

        Args:
            name: Screenshot name
        """
        if self.page:
            try:
                screenshot_path = ScreenshotManager.capture(
                    self.page,
                    name
                )

                allure.attach.file(
                    screenshot_path,
                    name=name,
                    attachment_type=allure.attachment_type.PNG
                )

                logger.info(f"Screenshot captured: {screenshot_path}")

            except Exception as e:
                logger.error(f"Failed to capture screenshot: {str(e)}")


class UITest(BaseTest):
    """Base class for UI tests"""

    def _setup(self):
        """Setup for UI tests"""
        super()._setup()

        # Create browser context and page
        self.context = DriverFactory.create_context()
        self.page = DriverFactory.create_page(self.context)

        logger.info("UI test setup completed")


class APITest(BaseTest):
    """Base class for API tests"""

    def _setup(self):
        """Setup for API tests"""
        super()._setup()

        # Create API client
        self.api_client = APIClient()

        logger.info("API test setup completed")


class IntegrationTest(UITest, APITest):
    """Base class for integration tests (UI + API)"""

    def _setup(self):
        """Setup for integration tests"""
        # Initialize both UI and API
        UITest._setup(self)

        # API client
        self.api_client = APIClient()

        logger.info("Integration test setup completed")