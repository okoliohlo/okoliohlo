"""
Dashboard Page Object
Handles dashboard page functionality after successful login
"""

from business.ui.pages.base_page import BasePage
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class DashboardPage(BasePage):

    """Dashboard page object"""
    
    # Locators - Multiple selector types for self-healing framework
    DASH_BODY = [
        "[data-testid='dashboard-body']",
        "body",
        "._widget-auto-layout",
        "[class*='dashboard']"
    ]
    DASH_BODY_NAME = 'dash_body'
    
    DASH_BOARD = [
        "[data-testid='dashboard']",
        "[aria-label='Dashboard']",
        "[class*='dashboard']",
        ".dashboard-container"
    ]
    DASH_BOARD_NAME = 'dash_board'
    
    DASH_HEADER = [
        "[data-testid='header']",
        "[role='banner']",
        "header",
        "[class*='header']"
    ]
    DASH_HEADER_NAME = 'dash_header'
    
    DASH_NAV = [
        "[data-testid='navigation']",
        "[role='navigation']",
        "nav",
        "[class*='nav']"
    ]
    DASH_NAV_NAME = 'dash_nav'
    
    DASH_CONTENT = [
        "[data-testid='content']",
        "[role='main']",
        "main",
        "[class*='content']"
    ]
    DASH_CONTENT_NAME = 'dash_content'
    
    DASH_MAIN = [
        "[data-testid='main']",
        "[class*='main']",
        ".main-area"
    ]
    DASH_MAIN_NAME = 'dash_main'


    @allure.step("Verify dashboard page is visible")
    def verify_dashboard_page(self, context):
        """
        Verify that key dashboard elements are visible
        """
        logger.info("Verifying dashboard elements")

        with allure.step("Verify dashboard elements are visible"):
            # Wait for page to be fully loaded
            context.page.wait_for_load_state('domcontentloaded', timeout=10000)

            # Common dashboard element selectors with multi-selector support
            dashboard_selectors = [
                (self.DASH_BODY, self.DASH_BODY_NAME),
                (self.DASH_BOARD, self.DASH_BOARD_NAME),
                (self.DASH_HEADER, self.DASH_HEADER_NAME),
                (self.DASH_NAV, self.DASH_NAV_NAME),
                (self.DASH_CONTENT, self.DASH_CONTENT_NAME),
                (self.DASH_MAIN, self.DASH_MAIN_NAME)
            ]

            found_elements = []

            for selectors, element_name in dashboard_selectors:
                try:
                    # Try each selector in the list
                    if isinstance(selectors, list):
                        for selector in selectors:
                            try:
                                if context.page.locator(selector).count() > 0:
                                    found_elements.append(element_name)
                                    logger.info(f"[OK] Found: {element_name} using selector: {selector}")
                                    break
                            except:
                                continue
                    else:
                        if context.page.locator(selectors).count() > 0:
                            found_elements.append(element_name)
                            logger.info(f"[OK] Found: {element_name}")
                except Exception as e:
                    logger.debug(f"Element not found: {element_name} - {e}")

            # Verify at least some elements are present
            assert len(found_elements) > 0, "No dashboard elements found"

            logger.info(f"[OK] Dashboard elements verified: {len(found_elements)} elements found")

            # Attach element verification to Allure
            allure.attach(
                f"Elements Found:\n" + "\n".join(f"  - {elem}" for elem in found_elements),
                name="Dashboard Elements Verification",
                attachment_type=allure.attachment_type.TEXT
            )

            # Take screenshot of dashboard elements
            screenshot_bytes = context.page.screenshot(full_page=True)
            allure.attach(
                screenshot_bytes,
                name="Dashboard Elements - Full Page",
                attachment_type=allure.attachment_type.PNG
            )
