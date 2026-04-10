"""
Step definitions for CareLink dashboard verification
Dashboard-specific verification steps
"""

from behave import given, when, then
from playwright.sync_api import expect
from config.config import config
from utilities.logger import get_logger
from business.ui.pages.dashboard_page import DashboardPage
import allure

logger = get_logger(__name__)


class DashboardSteps:
    """Helper class for dashboard step implementations"""

    @staticmethod
    def _ensure_dashboard_page(context):
        """
        Ensure dashboard_page is initialized in context

        Args:
            context: Behave context object
        """
        if not hasattr(context, 'dashboard_page'):
            context.dashboard_page = DashboardPage(context.page)
    
    @staticmethod
    def navigate_to_dashboard_with_session(context):
        """
        Navigate to dashboard by injecting authenticated cookies into browser context
        """
        logger.info("Navigating to dashboard with authenticated session")

        with allure.step("Navigate to dashboard with authenticated session"):
            # Get base URL
            base_url = config.get_base_url()
            dashboard_url = f"{base_url}/app/dashboard"

            # Convert cookies to Playwright format and add to context
            logger.info("Adding authentication cookies to browser context")

            playwright_cookies = []
            domain = base_url.replace("https://", "").replace("http://", "").split("/")[0]

            for cookie_name, cookie_value in context.auth_cookies.items():
                playwright_cookie = {
                    "name": cookie_name,
                    "value": cookie_value,
                    "domain": domain,
                    "path": "/"
                }
                playwright_cookies.append(playwright_cookie)
                logger.debug(f"Adding cookie: {cookie_name}")

            # Add cookies to the existing browser context
            context.browser_context.add_cookies(playwright_cookies)

            logger.info(f"Added {len(playwright_cookies)} cookies to browser context")
            logger.info(f"Navigating to: {dashboard_url}")

            # Navigate to dashboard (cookies already set)
            context.page.goto(dashboard_url, wait_until='networkidle', timeout=30000)

            # Wait for page to load
            context.page.wait_for_timeout(2000)

            current_url = context.page.url
            logger.info(f"Current URL: {current_url}")

            # Attach navigation info to Allure
            allure.attach(
                f"Dashboard URL: {dashboard_url}\n"
                f"Current URL: {current_url}\n"
                f"Cookies Injected: {len(playwright_cookies)}",
                name="Navigation Details",
                attachment_type=allure.attachment_type.TEXT
            )
    
    @staticmethod
    def verify_dashboard_elements(context):
        """
        Verify that key dashboard elements are visible using DashboardPage
        """
        DashboardSteps._ensure_dashboard_page(context)
        context.dashboard_page.verify_dashboard_page(context)
    
    @staticmethod
    def take_dashboard_screenshot(context):
        """
        Take a detailed screenshot of the dashboard for manual verification
        """
        logger.info("Taking dashboard screenshot for verification")

        with allure.step("Take dashboard screenshot for verification"):
            # Wait for any animations to complete
            context.page.wait_for_timeout(1000)

            # Take full page screenshot
            screenshot_bytes = context.page.screenshot(full_page=True)

            # Attach to Allure report
            allure.attach(
                screenshot_bytes,
                name=f"Dashboard Verification - {context.username}",
                attachment_type=allure.attachment_type.PNG
            )

            logger.info("[OK] Dashboard screenshot captured and attached to report")

            # Get page title
            page_title = context.page.title()

            # Get current URL
            current_url = context.page.url

            # Attach page details
            allure.attach(
                f"Page Title: {page_title}\n"
                f"URL: {current_url}\n"
                f"User: {context.username}\n"
                f"Timestamp: {context.page.evaluate('new Date().toISOString()')}",
                name="Dashboard Page Details",
                attachment_type=allure.attachment_type.TEXT
            )

            logger.info(f"[OK] Dashboard verification complete - Title: {page_title}")


# ============================================================================
# Behave Step Definitions (must be at module level)
# ============================================================================

@then('I navigate to the dashboard with authenticated session')
def step_navigate_to_dashboard_with_session(context):
    DashboardSteps.navigate_to_dashboard_with_session(context)


@then('I should see dashboard elements')
def step_verify_dashboard_elements(context):
    DashboardSteps.verify_dashboard_elements(context)


@then('I take a screenshot of the dashboard for verification')
def step_take_dashboard_screenshot(context):
    DashboardSteps.take_dashboard_screenshot(context)


