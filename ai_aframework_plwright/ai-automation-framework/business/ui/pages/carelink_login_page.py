"""
CareLink Login Page Object
Handles CareLink-specific login functionality
"""

from business.ui.pages.base_page import BasePage
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class CareLinkLoginPage(BasePage):
    """CareLink login page object with dynamic element handling"""

    # Locators - Multiple selector types for self-healing framework
    # Format: List of selectors in priority order (data-testid, aria-label, id, name, css)
    
    SIGN_IN_BUTTON = [
        "#landing-login-button-id",
        "[data-testid='login-btn']",
        "[aria-label='Sign in']",
        ".mat-legacy-primary-button",
        "button.mat-legacy-focus-indicator.form__button.mat-legacy-primary-button",
        "button:has-text('Sign in')"
    ]
    SIGN_IN_BUTTON_NAME = "sign_in_button"
    
    USERNAME_INPUT = [
        "#username",
        "[data-testid='username-input']",
        "[aria-label='Username']",
        "[name='username']",
        "input[type='text'][name='username']",
        "input.input",
        "input[type='text'], input[type='email']"
    ]
    USERNAME_INPUT_NAME = "username_input"
    
    PASSWORD_INPUT = [
        "#password",
        "[data-testid='password-input']",
        "[aria-label='Password']",
        "[name='password']",
        "input[type='password'][name='password']",
        "input.input",
        "input[type='password']"
    ]
    PASSWORD_INPUT_NAME = "password_input"

    LOGIN_BUTTON = [
        "[data-testid='submit-btn']",
        "[aria-label='Login']",
        "[name='action']",
        "button:has-text('Sign in')",
        "button[type='submit']",
        ".login-form button.primary"
    ]
    LOGIN_BUTTON_NAME = "login_button"
    
    LOGIN_FORM = [
        "[data-testid='login-form']",
        "form",
        "[class*='login-form']",
        "[data-testid*='login']"
    ]
    LOGIN_FORM_NAME = "login_form"

    def __init__(self, page):
        super().__init__(page)
        self.url = ""  # CareLink loads login on the main page
    
    @allure.step("Click Sign In button to open login form")
    def click_sign_in_button(self):
        """
        Click the initial Sign In button to reveal the login form
        """
        logger.info("Attempting to click Sign In button")
        
        # Click with self-healing support - try multiple selectors
        self.click_element_with_fallback(self.SIGN_IN_BUTTON, self.SIGN_IN_BUTTON_NAME)
        self.page.wait_for_timeout(1000)
        logger.info("Sign In button clicked")

    @allure.step("Open CareLink login page")
    def open(self):
        """Navigate to CareLink login page and open login form"""
        from config.config import Config
        config = Config()
        base_url = config.get_base_url()
        self.navigate_to(base_url)
        # Wait for page to be interactive
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("CareLink login page opened")
        
        # Click "Sign in" button to reveal login form
        self.click_sign_in_button()
    
    @allure.step("Enter username: {username}")
    def enter_username(self, username: str):
        """
        Enter username
        
        Args:
            username: Username to enter
        """
        logger.info(f"Attempting to enter username: {username}")
        
        # Enter username with self-healing support - try multiple selectors
        self.enter_text_with_fallback(self.USERNAME_INPUT, username, self.USERNAME_INPUT_NAME)
        logger.info("Username entered")
    
    @allure.step("Enter password: ****")
    def enter_password(self, password: str):
        """
        Enter password
        
        Args:
            password: Password to enter
        """
        logger.info("Attempting to enter password")
        
        # Enter password with self-healing support and masked screenshot - try multiple selectors
        self.enter_text_with_fallback(self.PASSWORD_INPUT, password, self.PASSWORD_INPUT_NAME, mask_text=True)
        logger.info("Password entered")
    
    @allure.step("Click login button")
    def click_login_button(self):
        """Click the login/submit button"""
        logger.info("Attempting to click login button")
        
        # Click login button with self-healing support - try multiple selectors
        self.click_element_with_fallback(self.LOGIN_BUTTON, self.LOGIN_BUTTON_NAME)
        self.wait_for_page_load()
        logger.info("Login button clicked")
    
    @allure.step("Perform login")
    def login(self, username: str, password: str):
        """
        Complete login flow
        
        Args:
            username: Username
            password: Password
        """
        logger.info(f"Performing login for user: {username}")
        self.enter_username(username)
        self.page.wait_for_timeout(500)
        self.enter_password(password)
        self.page.wait_for_timeout(500)
        self.click_login_button()
    
    @allure.step("Verify login form is visible")
    def is_login_form_visible(self) -> bool:
        """
        Check if login form is visible
        
        Returns:
            True if login form is visible, False otherwise
        """
        return (
            self.is_element_visible_with_fallback(self.LOGIN_FORM, self.LOGIN_FORM_NAME, timeout=5000) or
            self.is_element_visible_with_fallback(self.USERNAME_INPUT, self.USERNAME_INPUT_NAME, timeout=5000) or
            self.is_element_visible_with_fallback(self.PASSWORD_INPUT, self.PASSWORD_INPUT_NAME, timeout=5000)
        )
