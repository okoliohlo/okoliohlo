"""
Landing Page Object
Handles landing page functionality after successful login
"""

from business.ui.pages.base_page import BasePage
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class LandingPage(BasePage):
    """Landing page object"""

    # Locators - Multiple selector types for self-healing framework
    USER_MENU = [
        "[data-testid='user-menu']",
        "[data-test='user-menu']",
        "[aria-label='User menu']",
        "button[data-test='user-menu']",
        "button.user-menu"
    ]
    USER_MENU_NAME = "user_menu"

    LOGOUT_BUTTON = [
        "[data-testid='logout']",
        "[data-test='logout']",
        "[aria-label='Logout']",
        "button[data-test='logout']",
        "button:has-text('Logout')",
        "button:has-text('Sign out')"
    ]
    LOGOUT_BUTTON_NAME = "logout_button"

    LANDING_HEADER = [
        "[data-testid='dashboard-header']",
        "h1",
        "[class*='dashboard-header']",
        "header h1"
    ]
    LANDING_HEADER_NAME = "landing_header"

    NAVIGATION_MENU = [
        "[data-testid='navigation']",
        "[role='navigation']",
        "nav",
        "[class*='nav']"
    ]
    NAVIGATION_MENU_NAME = "navigation_menu"

    WELCOME_MESSAGE = [
        "[data-testid='welcome']",
        "[class*='welcome']",
        ".welcome-message"
    ]
    WELCOME_MESSAGE_NAME = "welcome_message"

    def __init__(self, page):
        super().__init__(page)
        self.url = "/dashboard"  # Typical landing URL

    @allure.step("Verify landing page is loaded")
    def is_landing_loaded(self) -> bool:
        """
        Check if landing page is loaded
        
        Returns:
            True if landing page is loaded, False otherwise
        """
        # Check for multiple possible landing page indicators
        return (
            self.is_element_visible_with_fallback(self.USER_MENU, self.USER_MENU_NAME, timeout=5000) or
            self.is_element_visible_with_fallback(self.LANDING_HEADER, self.LANDING_HEADER_NAME, timeout=5000) or
            self.is_element_visible_with_fallback(self.NAVIGATION_MENU, self.NAVIGATION_MENU_NAME, timeout=5000)
        )

    @allure.step("Get welcome message")
    def get_welcome_message(self) -> str:
        """
        Get welcome message text
        
        Returns:
            Welcome message text
        """
        if self.is_element_visible_with_fallback(self.WELCOME_MESSAGE, self.WELCOME_MESSAGE_NAME):
            return self.get_text(self.WELCOME_MESSAGE[0], self.WELCOME_MESSAGE_NAME)
        return ""

    @allure.step("Verify user is logged in")
    def is_user_logged_in(self) -> bool:
        """
        Check if user is logged in by verifying landing page elements
        
        Returns:
            True if user is logged in, False otherwise
        """
        return self.is_landing_loaded()

    @allure.step("Click user menu")
    def click_user_menu(self):
        """Click user menu to reveal logout option"""
        logger.info("Attempting to click user menu")
        
        # Check if element is visible first
        if not self.is_element_visible_with_fallback(self.USER_MENU, self.USER_MENU_NAME, timeout=5000):
            error_msg = f"User menu not found with selector: {self.USER_MENU}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Click user menu
        self.click_element_with_fallback(self.USER_MENU, self.USER_MENU_NAME)
        logger.info("User menu clicked")

    @allure.step("Logout from landing page")
    def logout(self):
        """
        Perform logout from landing page
        """
        logger.info("Attempting to logout")
        
        # Try to click user menu first (if logout is in dropdown)
        self.click_user_menu()
        self.page.wait_for_timeout(500)  # Wait for menu to appear
        
        # Check if logout button is visible
        if not self.is_element_visible_with_fallback(self.LOGOUT_BUTTON, self.LOGOUT_BUTTON_NAME, timeout=5000):
            error_msg = f"Logout button not found with selector: {self.LOGOUT_BUTTON}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Click logout button
        self.click_element_with_fallback(self.LOGOUT_BUTTON, self.LOGOUT_BUTTON_NAME)
        self.wait_for_page_load()
        logger.info("Logged out successfully")

    @allure.step("Navigate to section: {section_name}")
    def navigate_to_section(self, section_name: str):
        """
        Navigate to a specific section in the landing page
        
        Args:
            section_name: Name of the section to navigate to
        """
        logger.info(f"Attempting to navigate to section: {section_name}")
        
        # Generic navigation - can be customized based on actual landing page structure
        selector = f"a:has-text('{section_name}'), button:has-text('{section_name}')"
        
        # Check if element is visible first
        if not self.is_element_visible(selector, section_name, timeout=5000):
            error_msg = f"Section '{section_name}' not found with selector: {selector}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Click section
        self.click_element(selector, section_name)
        logger.info(f"Navigated to section: {section_name}")

    @allure.step("Verify navigation menu is visible")
    def is_navigation_visible(self) -> bool:
        """
        Check if navigation menu is visible
        
        Returns:
            True if navigation is visible, False otherwise
        """
        return self.is_element_visible_with_fallback(self.NAVIGATION_MENU, self.NAVIGATION_MENU_NAME)

    @allure.step("Get landing page title")
    def get_landing_title(self) -> str:
        """
        Get landing page title
        
        Returns:
            Landing page title
        """
        return self.get_page_title()

    @allure.step("Wait for landing page to load")
    def wait_for_landing(self, timeout: int = 30000):
        """
        Wait for landing page to fully load
        
        Args:
            timeout: Timeout in milliseconds
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        logger.info("Landing page loaded")
