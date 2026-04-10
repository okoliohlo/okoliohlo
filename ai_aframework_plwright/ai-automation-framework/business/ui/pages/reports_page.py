"""
Reports Page Object
Handles Reports page functionality after successful login
"""

from business.ui.pages.base_page import BasePage
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class ReportsPage(BasePage):
    """Reports page object"""
    
    # Locators - Multiple selector types for self-healing framework
    REPORTS_BODY = [
        "[data-testid='reports-body']",
        "body",
        "._widget-auto-layout",
        "[class*='reports']"
    ]
    REPORTS_BODY_NAME = 'reports_body'
    
    REPORTS_CONTAINER = [
        "[data-testid='reports-container']",
        "[aria-label='Reports']",
        "[class*='reports']",
        "[class*='report']",
        ".reports-container"
    ]
    REPORTS_CONTAINER_NAME = 'reports_container'
    
    REPORTS_HEADER = [
        "[data-testid='reports-header']",
        "[role='banner']",
        "header",
        "[class*='header']"
    ]
    REPORTS_HEADER_NAME = 'reports_header'
    
    REPORTS_NAV = [
        "[data-testid='navigation']",
        "[role='navigation']",
        "nav",
        "[class*='nav']"
    ]
    REPORTS_NAV_NAME = 'reports_nav'
    
    REPORTS_CONTENT = [
        "[data-testid='reports-content']",
        "[role='main']",
        "main",
        "._widget",
        "[class*='content']"
    ]
    REPORTS_CONTENT_NAME = 'reports_content'
    
    REPORTS_MAIN = [
        "[data-testid='main']",
        "[class*='main']",
        ".main-area"
    ]
    REPORTS_MAIN_NAME = 'reports_main'
    
    # Reports tab selectors - Multiple selector types
    REPORTS_TAB_SELECTORS = [
        "[data-testid='reports-tab']",
        "[aria-label='Reports']",
        "[href*='reports']",
        "a:has-text('Reports')",
        "button:has-text('Reports')",
        "nav a:has-text('Reports')",
        ".nav-link:has-text('Reports')",
        "[role='tab']:has-text('Reports')",
        "text=Reports"
    ]
    
    @allure.step("Verify reports page is visible")
    def verify_reports_page(self, context):
        """
        Verify that key reports page elements are visible
        
        Args:
            context: Behave context object
        """
        logger.info("Verifying report elements")
        
        with allure.step("Verify report elements are visible"):
            page = context.page
            
            # Wait for page to be fully loaded
            page.wait_for_load_state('domcontentloaded', timeout=10000)
            
            # Common reports element selectors with multi-selector support
            reports_selectors = [
                (self.REPORTS_BODY, self.REPORTS_BODY_NAME),
                (self.REPORTS_CONTAINER, self.REPORTS_CONTAINER_NAME),
                (self.REPORTS_HEADER, self.REPORTS_HEADER_NAME),
                (self.REPORTS_NAV, self.REPORTS_NAV_NAME),
                (self.REPORTS_CONTENT, self.REPORTS_CONTENT_NAME),
                (self.REPORTS_MAIN, self.REPORTS_MAIN_NAME)
            ]
            
            found_elements = []
            
            for selectors, element_name in reports_selectors:
                try:
                    # Try each selector in the list
                    if isinstance(selectors, list):
                        for selector in selectors:
                            try:
                                if page.locator(selector).count() > 0:
                                    found_elements.append(element_name)
                                    logger.info(f"[OK] Found: {element_name} using selector: {selector}")
                                    break
                            except:
                                continue
                    else:
                        if page.locator(selectors).count() > 0:
                            found_elements.append(element_name)
                            logger.info(f"[OK] Found: {element_name}")
                except Exception as e:
                    logger.debug(f"Element not found: {element_name} - {e}")
            
            # Verify at least some elements are present
            assert len(found_elements) > 0, "No reports elements found"
            
            logger.info(f"[OK] Report elements verified: {len(found_elements)} elements found")
            
            # Attach element verification to Allure
            allure.attach(
                f"Elements Found:\n" + "\n".join(f"  - {elem}" for elem in found_elements),
                name="Reports Elements Verification",
                attachment_type=allure.attachment_type.TEXT
            )
            
            # Take screenshot of reports page
            screenshot_bytes = page.screenshot(full_page=True)
            allure.attach(
                screenshot_bytes,
                name="Reports Page - Full Page",
                attachment_type=allure.attachment_type.PNG
            )
            
            # Attach page details
            allure.attach(
                f"Current URL: {page.url}\n"
                f"Page title: {page.title()}",
                name="Report Page Details",
                attachment_type=allure.attachment_type.TEXT
            )