"""
Step definitions for the Contact page button validation demo feature.
Uses the ProfilePage page object against https://profile.okoliohlo.com/
"""

from behave import when, then
from playwright.sync_api import expect
from business.ui.pages.profile_page import ProfilePage
from utilities.logger import get_logger
import allure

logger = get_logger(__name__)


# ============================================================================
# Helper
# ============================================================================

def _ensure_profile_page(context):
    """Lazily initialize ProfilePage on the context."""
    if not hasattr(context, "profile_page"):
        context.profile_page = ProfilePage(context.page)


# ============================================================================
# WHEN Steps
# ============================================================================

@when("I open the Profile page")
def step_open_profile_page(context):
    """Navigate to the Okoliohlo profile page."""
    _ensure_profile_page(context)

    with allure.step("Open Profile page"):
        context.profile_page.open()
        logger.info(f"Profile page opened — URL: {context.page.url}")


@when("I click the Contact button")
def step_click_contact_button(context):
    """Click the Contact navigation link to scroll to the contact section."""
    _ensure_profile_page(context)

    with allure.step("Click Contact navigation link"):
        context.profile_page.click_contact_link()
        logger.info("Contact link clicked — page should scroll to contact section")


# ============================================================================
# THEN Steps — Assertions
# ============================================================================

@then("I should see the Okoliohlo profile homepage")
def step_verify_profile_homepage(context):
    """Verify that the profile homepage is fully loaded."""
    _ensure_profile_page(context)

    with allure.step("Verify Okoliohlo profile homepage"):
        # Wait for full page load
        context.page.wait_for_load_state("domcontentloaded")

        # URL check
        current_url = context.page.url
        assert "profile.okoliohlo.com" in current_url, (
            f"Expected URL to contain 'profile.okoliohlo.com', got: {current_url}"
        )

        # Page title check
        title = context.page.title()
        assert "Oleksii Koliohlo" in title, (
            f"Expected title to contain 'Oleksii Koliohlo', got: {title}"
        )

        # Visual structure check
        assert context.profile_page.is_homepage_loaded(), (
            "Profile homepage is not fully loaded (navbar or hero section missing)"
        )

        # Brand text check
        brand = context.profile_page.get_brand_text()
        assert "Oleksii Koliohlo" in brand, (
            f"Expected brand text 'Oleksii Koliohlo', got: {brand}"
        )

        logger.info("Profile homepage verified successfully")

        # Attach screenshot to Allure
        screenshot_bytes = context.page.screenshot(full_page=False)
        allure.attach(
            screenshot_bytes,
            name="Okoliohlo profile homepage",
            attachment_type=allure.attachment_type.PNG,
        )


@then("I should see the Contact form")
def step_verify_contact_form(context):
    """Verify the Contact section and form are visible after scrolling."""
    _ensure_profile_page(context)

    with allure.step("Verify Contact section and form"):
        # Contact section is in viewport
        assert context.profile_page.is_contact_section_visible(), (
            "Contact section is not visible after clicking Contact link"
        )

        # Contact heading
        assert context.profile_page.is_contact_title_visible(), (
            "Contact title heading is not visible"
        )
        title_text = context.profile_page.get_contact_title_text()
        assert "Contact" in title_text, (
            f"Expected 'Contact' in title, got: {title_text}"
        )

        # Contact form with all fields
        assert context.profile_page.is_contact_form_visible(), (
            "Contact form is not fully visible (missing form, inputs, or submit button)"
        )

        # LinkedIn link
        assert context.profile_page.is_linkedin_visible(), (
            "LinkedIn profile link is not visible in the contact section"
        )

        logger.info("Contact form verified — all fields and links present")

        # Attach final screenshot
        screenshot_bytes = context.page.screenshot(full_page=False)
        allure.attach(
            screenshot_bytes,
            name="Contact form visible",
            attachment_type=allure.attachment_type.PNG,
        )
