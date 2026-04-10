"""
Step definitions for CareLink reports verification
Reports-specific verification steps
"""

from behave import given, when, then
from playwright.sync_api import expect
from config.config import config
from utilities.logger import get_logger
from business.ui.pages.reports_page import ReportsPage
import allure

logger = get_logger(__name__)


class ReportsSteps:
    """Helper class for reports step implementations"""

    @staticmethod
    def _ensure_reports_page(context):
        """
        Ensure reports_page is initialized in context

        Args:
            context: Behave context object
        """
        if not hasattr(context, 'reports_page'):
            context.reports_page = ReportsPage(context.page)

    @staticmethod
    def click_reports_tab(context):
        """
        Click on the reports tab in the navigation
        """


        logger.info("Clicking on reports tab")
        # Get selectors from ReportsPage
        reports_tab_selectors = ReportsPage.REPORTS_TAB_SELECTORS


        with allure.step("Click on reports tab"):
            page = context.page
            
            # # Log all available links for debugging
            # all_links = page.locator('a').all_text_contents()
            # logger.info(f"Available links on page: {all_links[:10]}")  # First 10 links
            


            clicked = False
            for selector in reports_tab_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logger.info(f"Found reports tab with selector: {selector}")
                        page.locator(selector).first.click()
                        page.wait_for_timeout(2000)
                        clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not clicked:
                logger.warning("Reports tab not found with any selector, taking screenshot")
                screenshot_bytes = page.screenshot()
                allure.attach(
                    screenshot_bytes,
                    name="Reports Tab Not Found",
                    attachment_type=allure.attachment_type.PNG
                )
                raise Exception("Could not find reports tab")
            
            logger.info(f"Navigated to: {page.url}")
            
            allure.attach(
                f"Reports tab clicked\nCurrent URL: {page.url}",
                name="Reports Navigation",
                attachment_type=allure.attachment_type.TEXT
            )

    @staticmethod
    def verify_reports_elements(context):
        """
        Verify that key reports page elements are visible using ReportsPage
        """
        ReportsSteps._ensure_reports_page(context)
        context.reports_page.verify_reports_page(context)


# ============================================================================
# Behave Step Definitions (must be at module level)
# ============================================================================

@then('I click on the reports tab')
def step_click_reports_tab(context):
    ReportsSteps.click_reports_tab(context)


@then('I should see report elements')
def step_verify_report_elements(context):
    ReportsSteps.verify_reports_elements(context)