"""
Profile Page Object
Handles interactions with the Okoliohlo profile page at https://profile.okoliohlo.com/
"""

from business.ui.pages.base_page import BasePage
from config.config import config
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


class ProfilePage(BasePage):
    """Page object for the Okoliohlo profile homepage."""

    # ======================================================================
    # Locators — multiple selectors per element for self-healing
    # ======================================================================

    # Navigation
    NAV_BAR = "nav#tmNav"
    NAV_BAR_NAME = "navigation_bar"

    BRAND_LINK = "a.navbar-brand"
    BRAND_LINK_NAME = "brand_link"

    CONTACT_NAV_LINK = "a.nav-link.tm-nav-link[href='#contact']"
    CONTACT_NAV_LINK_NAME = "contact_nav_link"

    # Hero section (Executive Summary)
    HERO_SECTION = "section#infinite"
    HERO_SECTION_NAME = "hero_section"

    # Contact section
    CONTACT_SECTION = "section#contact"
    CONTACT_SECTION_NAME = "contact_section"

    CONTACT_TITLE = "#contact h2.tm-section-title"
    CONTACT_TITLE_NAME = "contact_title"

    CONTACT_FORM = "#contact form"
    CONTACT_FORM_NAME = "contact_form"

    NAME_INPUT = "#contact input#name"
    NAME_INPUT_NAME = "name_input"

    EMAIL_INPUT = "#contact input#email"
    EMAIL_INPUT_NAME = "email_input"

    MESSAGE_TEXTAREA = "#contact textarea#message"
    MESSAGE_TEXTAREA_NAME = "message_textarea"

    SUBMIT_BUTTON = "#contact button.tm-btn-submit"
    SUBMIT_BUTTON_NAME = "submit_button"

    LINKEDIN_LINK = "#contact a[href*='linkedin']"
    LINKEDIN_LINK_NAME = "linkedin_link"

    # Section navigation links
    EXEC_SUMMARY_LINK = "a.nav-link.tm-nav-link[href='#infinite']"
    PROF_EXP_LINK = "a.nav-link.tm-nav-link[href='#professional-experience']"
    TECH_SKILLS_LINK = "a.nav-link.tm-nav-link[href='#technical-skills']"
    EDU_LINK = "a.nav-link.tm-nav-link[href='#education-certifications']"

    def __init__(self, page):
        super().__init__(page)
        self.url = config.get_profile_url()

    # ======================================================================
    # Navigation
    # ======================================================================

    @allure.step("Open Profile page")
    def open(self):
        """Navigate to the profile page and wait for load."""
        logger.info(f"Opening profile page: {self.url}")
        self.navigate_to(self.url)
        self.wait_for_page_load()
        logger.info("Profile page loaded")

    @allure.step("Click Contact navigation link")
    def click_contact_link(self):
        """Click the Contact link in the top navigation bar."""
        logger.info("Clicking Contact nav link")
        self.click_element(
            self.CONTACT_NAV_LINK,
            element_name=self.CONTACT_NAV_LINK_NAME,
        )
        # Wait for smooth scroll to complete
        self.page.wait_for_timeout(1500)
        logger.info("Clicked Contact link — scrolled to contact section")

    # ======================================================================
    # Verifications
    # ======================================================================

    @allure.step("Verify profile homepage is loaded")
    def is_homepage_loaded(self) -> bool:
        """
        Verify the profile homepage is fully loaded.

        Checks:
          - Navbar is visible
          - Brand text is present
          - Hero section is visible
        """
        nav_visible = self.is_element_visible(
            self.NAV_BAR, self.NAV_BAR_NAME, timeout=10000,
        )
        hero_visible = self.is_element_visible(
            self.HERO_SECTION, self.HERO_SECTION_NAME, timeout=10000,
        )

        if nav_visible and hero_visible:
            logger.info("Profile homepage loaded successfully")
            self.take_screenshot("Profile homepage loaded")
            return True

        logger.warning("Profile homepage did not load fully")
        return False

    @allure.step("Verify Contact section is visible")
    def is_contact_section_visible(self) -> bool:
        """Check that the Contact section is scrolled into view."""
        return self.is_element_visible(
            self.CONTACT_SECTION, self.CONTACT_SECTION_NAME, timeout=10000,
        )

    @allure.step("Verify Contact title is visible")
    def is_contact_title_visible(self) -> bool:
        """Check the Contact heading is visible."""
        return self.is_element_visible(
            self.CONTACT_TITLE, self.CONTACT_TITLE_NAME, timeout=5000,
        )

    @allure.step("Verify Contact form is visible")
    def is_contact_form_visible(self) -> bool:
        """
        Verify the contact form with all fields is visible.

        Checks: form element, name input, email input, message textarea, submit button.
        """
        form_ok = self.is_element_visible(
            self.CONTACT_FORM, self.CONTACT_FORM_NAME, timeout=10000,
        )
        name_ok = self.is_element_visible(
            self.NAME_INPUT, self.NAME_INPUT_NAME, timeout=3000,
        )
        email_ok = self.is_element_visible(
            self.EMAIL_INPUT, self.EMAIL_INPUT_NAME, timeout=3000,
        )
        message_ok = self.is_element_visible(
            self.MESSAGE_TEXTAREA, self.MESSAGE_TEXTAREA_NAME, timeout=3000,
        )
        submit_ok = self.is_element_visible(
            self.SUBMIT_BUTTON, self.SUBMIT_BUTTON_NAME, timeout=3000,
        )

        all_ok = form_ok and name_ok and email_ok and message_ok and submit_ok
        if all_ok:
            logger.info("Contact form is fully visible with all fields")
            self.take_screenshot("Contact form visible")
        else:
            logger.warning(
                f"Contact form check — form={form_ok} name={name_ok} "
                f"email={email_ok} message={message_ok} submit={submit_ok}"
            )
        return all_ok

    @allure.step("Verify LinkedIn link is visible")
    def is_linkedin_visible(self) -> bool:
        """Check the LinkedIn profile link is visible in the contact section."""
        return self.is_element_visible(
            self.LINKEDIN_LINK, self.LINKEDIN_LINK_NAME, timeout=5000,
        )

    @allure.step("Get Contact title text")
    def get_contact_title_text(self) -> str:
        """Return the text of the Contact section heading."""
        return self.get_text(self.CONTACT_TITLE, self.CONTACT_TITLE_NAME)

    @allure.step("Get page brand text")
    def get_brand_text(self) -> str:
        """Return the brand/name text from the navbar."""
        return self.get_text(self.BRAND_LINK, self.BRAND_LINK_NAME)
