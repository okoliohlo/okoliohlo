"""
Authentication Flow
High-level authentication workflows
"""

from business.ui.pages.carelink_login_page import CareLinkLoginPage
from business.ui.pages.landing_page import LandingPage
from config.config import Config
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class AuthFlow:
    """Authentication workflow"""

    def __init__(self, page):
        self.page = page
        self.login_page = CareLinkLoginPage(page)
        self.landing_page = LandingPage(page)

    @allure.step("Complete login flow with standard user")
    def login_as_standard_user(self):
        """Login with standard user credentials"""
        config = Config()
        credentials = config.get_credentials("standard")
        self.login_with_credentials(
            credentials["username"],
            credentials["password"]
        )

    @allure.step("Complete login flow with admin user")
    def login_as_admin(self):
        """Login with admin credentials"""
        config = Config()
        credentials = config.get_credentials("admin")
        self.login_with_credentials(
            credentials["username"],
            credentials["password"]
        )

    @allure.step("Login with username: {username}")
    def login_with_credentials(self, username: str, password: str):
        """
        Complete login flow

        Args:
            username: Username
            password: Password

        Returns:
            True if login successful, False otherwise
        """
        logger.info(f"Starting login flow for: {username}")

        self.login_page.open()
        self.login_page.login(username, password)

        # Verify login successful
        if self.landing_page.is_landing_loaded():
            logger.info("Login successful")
            return True
        else:
            error_message = self.login_page.get_error_message()
            logger.error(f"Login failed: {error_message}")
            return False

    @allure.step("Complete logout flow")
    def logout(self):
        """Complete logout flow"""
        logger.info("Starting logout flow")
        self.login_page.logout()