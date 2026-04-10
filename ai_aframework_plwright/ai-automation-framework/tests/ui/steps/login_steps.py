"""
Step definitions for CareLink login feature
Using Behave with Playwright and Page Object Model

Note: Common authentication steps (API auth, environment setup) are in common_steps.py
"""

from behave import given, when, then
from playwright.sync_api import expect
from config.config import config, Config
from business.ui.pages.carelink_login_page import CareLinkLoginPage
from business.ui.flows.auth_flow import AuthFlow
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class LoginSteps:
    """Helper class for login step implementations"""
    
    @staticmethod
    def _ensure_login_page(context):
        """
        Ensure login_page is initialized in context
        
        Args:
            context: Behave context object
        """
        if not hasattr(context, 'login_page'):
            context.login_page = CareLinkLoginPage(context.page)
    
    @staticmethod
    def navigate_to_login_page(context):
        """Navigate directly to the login page"""
        LoginSteps._ensure_login_page(context)
        context.login_page.open()
        logger.info("Navigated to login page")
    
    @staticmethod
    def on_carelink_homepage(context):
        """Navigate to CareLink homepage"""
        base_url = config.get_base_url()
        context.page.goto(base_url)
        context.page.wait_for_load_state('networkidle')
        logger.info(f"Opened CareLink homepage: {base_url}")
    
    @staticmethod
    def open_carelink_page(context):
        """Open the CareLink application homepage"""
        base_url = config.get_base_url()
        context.page.goto(base_url)
        context.page.wait_for_load_state('networkidle')
        logger.info(f"Opened CareLink page: {base_url}")
    
    @staticmethod
    def click_sign_in_button(context):
        """Click the sign in button to reveal login form"""
        LoginSteps._ensure_login_page(context)
        
        context.login_page.click_sign_in_button()
        context.page.wait_for_timeout(2000)  # Wait for form to appear
        logger.info("Clicked sign in button")
    
    @staticmethod
    def enter_username(context, username):
        """Enter username in the login form"""
        LoginSteps._ensure_login_page(context)
        
        context.login_page.enter_username(username)
        logger.info(f"Entered username: {username}")
    
    @staticmethod
    def enter_password(context, password):
        """Enter password in the login form"""
        LoginSteps._ensure_login_page(context)
        context.login_page.enter_password(password)
        logger.info("Entered password")
    
    @staticmethod
    def click_login_button(context):
        """Click the login button to submit credentials"""
        LoginSteps._ensure_login_page(context)
        
        context.login_page.click_login_button()
        logger.info("Clicked login button")
    
    @staticmethod
    def login_as_user_type(context, user_type):
        """
        Login using credentials from config for specified user type
        
        Args:
            user_type: Type of user (standard, admin, premium, etc.)
        """
        LoginSteps._ensure_login_page(context)
        
        # Get credentials from config
        credentials = config.get_credentials(user_type)
        
        if not credentials:
            raise ValueError(f"No credentials found for user type: {user_type}")
        
        username = credentials.get('username')
        password = credentials.get('password')
        
        logger.info(f"Logging in as {user_type} user: {username}")
        
        # Perform login
        context.login_page.enter_username(username)
        context.login_page.enter_password(password)
        context.login_page.click_login_button()
        
        logger.info(f"Login completed for {user_type} user")
    
    @staticmethod
    def verify_carelink_homepage(context):
        """Verify that CareLink homepage is loaded"""
        with allure.step("Verify CareLink homepage loaded"):
            context.page.wait_for_load_state('domcontentloaded')
            
            current_url = context.page.url
            base_url = config.get_base_url()
            
            assert base_url in current_url, f"Expected URL to contain {base_url}, but got {current_url}"
            logger.info(f"Successfully loaded CareLink homepage: {current_url}")
            
            # Take screenshot of homepage
            screenshot_bytes = context.page.screenshot(full_page=False)
            allure.attach(
                screenshot_bytes,
                name="CareLink homepage loaded",
                attachment_type=allure.attachment_type.PNG
            )
            logger.info("Screenshot captured: CareLink homepage")
    
    @staticmethod
    def verify_navigation_to_login(context):
        """Verify navigation to login page"""
        context.page.wait_for_load_state('domcontentloaded')
        current_url = context.page.url
        
        assert current_url is not None, "Page URL is None"
        logger.info(f"Navigated to: {current_url}")
    
    @staticmethod
    def verify_login_form_visible(context):
        """Verify that login form is visible"""
        LoginSteps._ensure_login_page(context)
        
        # Wait for page to be fully loaded
        context.page.wait_for_load_state("networkidle", timeout=15000)
        
        # Verify login form is present
        assert context.login_page.is_login_form_visible(), "Login form is not visible"
        logger.info("Login form is visible")
    
    @staticmethod
    def verify_successful_login(context):
        """Verify successful login by checking URL change or dashboard elements"""
        with allure.step("Verify successful login"):
            context.page.wait_for_load_state('networkidle', timeout=30000)
            
            current_url = context.page.url
            
            # Check if we navigated away from login page
            try:
                assert 'login' not in current_url.lower(), f"Still on login page: {current_url}"
                logger.info(f"Successfully logged in. Current URL: {current_url}")
                
                # Take screenshot of successful login state
                screenshot_bytes = context.page.screenshot(full_page=False)
                allure.attach(
                    screenshot_bytes,
                    name="Login successful - Dashboard",
                    attachment_type=allure.attachment_type.PNG
                )
                logger.info("Screenshot captured: Login successful")
                
            except AssertionError as e:
                # Take screenshot of failure
                screenshot_bytes = context.page.screenshot(full_page=False)
                allure.attach(
                    screenshot_bytes,
                    name="Login failed - Still on login page",
                    attachment_type=allure.attachment_type.PNG
                )
                logger.error(f"Login verification failed: {e}")
                raise


# ============================================================================
# Behave Step Definitions (must be at module level)
# ============================================================================

@given('I am on the login page')
def step_navigate_to_login_page(context):
    LoginSteps.navigate_to_login_page(context)


@given('I am on the CareLink homepage')
def step_on_carelink_homepage(context):
    LoginSteps.on_carelink_homepage(context)


@when('I open the CareLink page')
def step_open_carelink_page(context):
    LoginSteps.open_carelink_page(context)


@when('I click the sign in button')
def step_click_sign_in_button(context):
    LoginSteps.click_sign_in_button(context)


@when('I enter username "{username}"')
def step_enter_username(context, username):
    LoginSteps.enter_username(context, username)


@when('I enter password "{password}"')
def step_enter_password(context, password):
    LoginSteps.enter_password(context, password)


@when('I click the login button')
def step_click_login_button(context):
    LoginSteps.click_login_button(context)


@when('I login as "{user_type}" user')
def step_login_as_user_type(context, user_type):
    LoginSteps.login_as_user_type(context, user_type)


# ============================================================================
# THEN Steps - Assertions/Verifications
# ============================================================================

@then('I should see the CareLink homepage')
def step_verify_carelink_homepage(context):
    LoginSteps.verify_carelink_homepage(context)


@then('I should navigate to the login page')
def step_verify_navigation_to_login(context):
    LoginSteps.verify_navigation_to_login(context)


@then('I should see the login form')
def step_verify_login_form_visible(context):
    LoginSteps.verify_login_form_visible(context)


@then('I should be logged in successfully')
def step_verify_successful_login(context):
    LoginSteps.verify_successful_login(context)
