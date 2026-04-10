"""
Base Page Object
Provides common methods for all page objects
"""

from typing import Optional, List
from playwright.sync_api import Page, Locator, expect
from ai.self_healing.source_updater import SourceUpdater
from utilities.logger import get_logger
import allure
import io

logger = get_logger(__name__)


class BasePage:
    """
    Base class for all page objects
    Implements common page interactions with integrated self-healing
    """

    def __init__(self, page: Page):
        """
        Initialize base page

        Args:
            page: Playwright Page instance (with self-healing if enabled)
        """
        self.page = page

    def take_screenshot(self, name: str = "screenshot", attach_to_allure: bool = True):
        """
        Take screenshot and optionally attach to Allure report

        Args:
            name: Screenshot name
            attach_to_allure: Whether to attach to Allure report

        Returns:
            Screenshot bytes
        """
        try:
            screenshot_bytes = self.page.screenshot(full_page=False)
            
            if attach_to_allure:
                allure.attach(
                    screenshot_bytes,
                    name=name,
                    attachment_type=allure.attachment_type.PNG
                )
                logger.debug(f"Screenshot attached to Allure: {name}")
            
            return screenshot_bytes
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {str(e)}")
            return None

    @allure.step("Navigate to {url}")
    def navigate_to(self, url: str):
        """
        Navigate to URL

        Args:
            url: Target URL
        """
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until="networkidle")

    @allure.step("Click element: {element_name}")
    def click_element(self, selector: str, element_name: str = None, take_screenshot: bool = True):
        """
        Click element with self-healing

        Args:
            selector: Element selector
            element_name: Logical name for element
            take_screenshot: Whether to take screenshot after click
        """
        logger.info(f"Clicking element: {element_name or selector}")
        
        # Try with self-healing if enabled and element_name provided
        if element_name and hasattr(self.page, '_healing_engine'):
            try:
                locator = self.page.locator(selector)
                locator.click()
                # Record success for future healing
                self.page._healing_engine.record_success(element_name, selector, locator)
                
                # Take screenshot after click
                if take_screenshot:
                    self.page.wait_for_timeout(500)  # Brief wait for UI update
                    self.take_screenshot(f"After clicking: {element_name}")
            except Exception as e:
                logger.warning(f"Locator failed, attempting self-healing: {str(e)}")
                # Attempt healing
                healing_result = self.page._healing_engine.heal(selector, element_name)
                if healing_result.success:
                    logger.info(f"Self-healing successful! New selector: {healing_result.new_selector}")
                    healing_result.locator.click()
                    
                    # Controlled source code update
                    SourceUpdater().update_if_approved(
                        page_object=self,
                        old_selector=selector,
                        new_selector=healing_result.new_selector,
                        element_name=element_name,
                        confidence=healing_result.confidence,
                        strategy=healing_result.strategy or "",
                    )
                    
                    if take_screenshot:
                        self.page.wait_for_timeout(500)
                        self.take_screenshot(f"After clicking (healed): {element_name}")
                else:
                    raise
        else:
            # No self-healing, just click
            locator = self.page.locator(selector)
            locator.click()
            
            if take_screenshot:
                self.page.wait_for_timeout(500)
                self.take_screenshot(f"After clicking: {element_name or 'element'}")

    @allure.step("Click element with fallback: {element_name}")
    def click_element_with_fallback(self, selectors: List[str], element_name: str = None, take_screenshot: bool = True):
        """
        Click element trying multiple selectors in priority order
        
        Args:
            selectors: List of selectors to try (or single selector string)
            element_name: Logical name for element
            take_screenshot: Whether to take screenshot after click
        """
        # Handle single selector string
        if isinstance(selectors, str):
            return self.click_element(selectors, element_name, take_screenshot)
        
        logger.info(f"Clicking element with fallback: {element_name} ({len(selectors)} selectors)")
        
        last_error = None
        for i, selector in enumerate(selectors):
            try:
                logger.debug(f"Trying selector {i+1}/{len(selectors)}: {selector}")
                self.click_element(selector, element_name, take_screenshot)
                logger.info(f"✓ Successfully clicked using selector: {selector}")
                return
            except Exception as e:
                last_error = e
                logger.debug(f"✗ Selector failed: {selector} - {str(e)}")
                continue
        
        # All selectors failed
        logger.error(f"All {len(selectors)} selectors failed for: {element_name}")
        raise last_error if last_error else Exception(f"Could not click element: {element_name}")

    @allure.step("Enter text: {element_name}")
    def enter_text(self, selector: str, text: str, element_name: str = None, take_screenshot: bool = True, mask_text: bool = False):
        """
        Enter text in input field

        Args:
            selector: Element selector
            text: Text to enter
            element_name: Logical name for element
            take_screenshot: Whether to take screenshot after entering text
            mask_text: Whether to mask the text in screenshot (for passwords)
        """
        logger.info(f"Entering text in: {element_name or selector}")
        
        # Try with self-healing if enabled and element_name provided
        if element_name and hasattr(self.page, '_healing_engine'):
            try:
                locator = self.page.locator(selector)
                locator.fill(text)
                # Record success for future healing
                self.page._healing_engine.record_success(element_name, selector, locator)
                
                # Take screenshot after entering text
                if take_screenshot:
                    screenshot_name = f"After entering: {element_name}"
                    if mask_text:
                        screenshot_name += " (masked)"
                    self.take_screenshot(screenshot_name)
            except Exception as e:
                logger.warning(f"Locator failed, attempting self-healing: {str(e)}")
                # Attempt healing
                healing_result = self.page._healing_engine.heal(selector, element_name)
                if healing_result.success:
                    logger.info(f"Self-healing successful! New selector: {healing_result.new_selector}")
                    healing_result.locator.fill(text)
                    
                    if take_screenshot:
                        screenshot_name = f"After entering (healed): {element_name}"
                        if mask_text:
                            screenshot_name += " (masked)"
                        self.take_screenshot(screenshot_name)
                else:
                    raise
        else:
            # No self-healing, just fill
            locator = self.page.locator(selector)
            locator.fill(text)
            
            if take_screenshot:
                screenshot_name = f"After entering: {element_name or 'text'}"
                if mask_text:
                    screenshot_name += " (masked)"
                self.take_screenshot(screenshot_name)

    @allure.step("Enter text with fallback: {element_name}")
    def enter_text_with_fallback(self, selectors: List[str], text: str, element_name: str = None, 
                                  take_screenshot: bool = True, mask_text: bool = False):
        """
        Enter text trying multiple selectors in priority order
        
        Args:
            selectors: List of selectors to try (or single selector string)
            text: Text to enter
            element_name: Logical name for element
            take_screenshot: Whether to take screenshot after entering text
            mask_text: Whether to mask the text in screenshot (for passwords)
        """
        # Handle single selector string
        if isinstance(selectors, str):
            return self.enter_text(selectors, text, element_name, take_screenshot, mask_text)
        
        logger.info(f"Entering text with fallback: {element_name} ({len(selectors)} selectors)")
        
        last_error = None
        for i, selector in enumerate(selectors):
            try:
                logger.debug(f"Trying selector {i+1}/{len(selectors)}: {selector}")
                self.enter_text(selector, text, element_name, take_screenshot, mask_text)
                logger.info(f"✓ Successfully entered text using selector: {selector}")
                return
            except Exception as e:
                last_error = e
                logger.debug(f"✗ Selector failed: {selector} - {str(e)}")
                continue
        
        # All selectors failed
        logger.error(f"All {len(selectors)} selectors failed for: {element_name}")
        raise last_error if last_error else Exception(f"Could not enter text in element: {element_name}")

    @allure.step("Get text from: {element_name}")
    def get_text(self, selector: str, element_name: str = None) -> str:
        """
        Get text from element

        Args:
            selector: Element selector
            element_name: Logical name for element

        Returns:
            Text content
        """
        logger.info(f"Getting text from: {element_name or selector}")
        locator = self.page.locator(selector)
        return locator.text_content()

    @allure.step("Verify element visible: {element_name}")
    def is_element_visible(self, selector: str, element_name: str = None, timeout: int = 5000, take_screenshot: bool = True) -> bool:
        """
        Check if element is visible

        Args:
            selector: Element selector
            element_name: Logical name for element
            timeout: Timeout in milliseconds
            take_screenshot: Whether to take screenshot for verification

        Returns:
            True if visible, False otherwise
        """
        # Try with self-healing if enabled and element_name provided
        if element_name and hasattr(self.page, '_healing_engine'):
            try:
                locator = self.page.locator(selector)
                locator.wait_for(state="visible", timeout=timeout)
                # Record success for future healing
                self.page._healing_engine.record_success(element_name, selector, locator)
                
                # Take screenshot for verification
                if take_screenshot:
                    self.take_screenshot(f"Verified: {element_name}")
                
                return True
            except Exception:
                logger.debug(f"Locator failed, attempting self-healing for: {element_name}")
                # Attempt healing
                healing_result = self.page._healing_engine.heal(selector, element_name)
                if healing_result.success:
                    logger.info(f"Self-healing successful! New selector: {healing_result.new_selector}")
                    try:
                        healing_result.locator.wait_for(state="visible", timeout=timeout)
                        
                        # Take screenshot after healing
                        if take_screenshot:
                            self.take_screenshot(f"Verified (healed): {element_name}")
                        
                        return True
                    except Exception:
                        if take_screenshot:
                            self.take_screenshot(f"Failed: {element_name}")
                        return False
                
                if take_screenshot:
                    self.take_screenshot(f"Failed: {element_name}")
                return False
        else:
            # No self-healing
            try:
                locator = self.page.locator(selector)
                locator.wait_for(state="visible", timeout=timeout)
                
                # Take screenshot for verification
                if take_screenshot:
                    self.take_screenshot(f"Verified: {element_name or 'element'}")
                
                return True
            except Exception:
                logger.debug(f"Element not visible: {element_name or selector}")
                
                if take_screenshot:
                    self.take_screenshot(f"Failed: {element_name or 'element'}")
                
                return False

    @allure.step("Verify element visible with fallback: {element_name}")
    def is_element_visible_with_fallback(self, selectors: List[str], element_name: str = None, 
                                          timeout: int = 5000, take_screenshot: bool = True) -> bool:
        """
        Check if element is visible trying multiple selectors in priority order
        
        Args:
            selectors: List of selectors to try (or single selector string)
            element_name: Logical name for element
            timeout: Timeout in milliseconds
            take_screenshot: Whether to take screenshot for verification
            
        Returns:
            True if visible, False otherwise
        """
        # Handle single selector string
        if isinstance(selectors, str):
            return self.is_element_visible(selectors, element_name, timeout, take_screenshot)
        
        logger.debug(f"Checking visibility with fallback: {element_name} ({len(selectors)} selectors)")
        
        for i, selector in enumerate(selectors):
            try:
                logger.debug(f"Trying selector {i+1}/{len(selectors)}: {selector}")
                if self.is_element_visible(selector, element_name, timeout, take_screenshot):
                    logger.info(f"✓ Element visible using selector: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"✗ Selector failed: {selector} - {str(e)}")
                continue
        
        # All selectors failed
        logger.debug(f"Element not visible with any of {len(selectors)} selectors: {element_name}")
        return False

    @allure.step("Wait for element: {element_name}")
    def wait_for_element(self, selector: str, element_name: str = None,
                         state: str = "visible", timeout: int = 30000):
        """
        Wait for element to reach state

        Args:
            selector: Element selector
            element_name: Logical name for element
            state: Element state (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds
        """
        logger.info(f"Waiting for element: {element_name or selector} to be {state}")
        locator = self.page.locator(selector)
        locator.wait_for(state=state, timeout=timeout)

    @allure.step("Select dropdown option: {option}")
    def select_dropdown(self, selector: str, option: str, element_name: str = None):
        """
        Select option from dropdown

        Args:
            selector: Dropdown selector
            option: Option to select
            element_name: Logical name for element
        """
        logger.info(f"Selecting option '{option}' from: {element_name or selector}")
        locator = self.page.locator(selector)
        locator.select_option(option)

    @allure.step("Check checkbox: {element_name}")
    def check_checkbox(self, selector: str, element_name: str = None):
        """Check checkbox if not already checked"""
        locator = self.page.locator(selector)
        if not locator.is_checked():
            locator.check()
            logger.info(f"Checkbox checked: {element_name or selector}")

    @allure.step("Uncheck checkbox: {element_name}")
    def uncheck_checkbox(self, selector: str, element_name: str = None):
        """Uncheck checkbox if checked"""
        locator = self.page.locator(selector)
        if locator.is_checked():
            locator.uncheck()
            logger.info(f"Checkbox unchecked: {element_name or selector}")

    @allure.step("Get attribute: {attribute_name} from {element_name}")
    def get_attribute(self, selector: str, attribute_name: str, element_name: str = None) -> str:
        """
        Get element attribute value

        Args:
            selector: Element selector
            attribute_name: Attribute name
            element_name: Logical name for element

        Returns:
            Attribute value
        """
        locator = self.page.locator(selector)
        return locator.get_attribute(attribute_name)

    @allure.step("Scroll to element: {element_name}")
    def scroll_to_element(self, selector: str, element_name: str = None):
        """Scroll element into view"""
        locator = self.page.locator(selector)
        locator.scroll_into_view_if_needed()
        logger.info(f"Scrolled to: {element_name or selector}")

    @allure.step("Wait for page load")
    def wait_for_page_load(self):
        """Wait for page to fully load"""
        self.page.wait_for_load_state("networkidle")
        logger.info("Page loaded")

    @allure.step("Execute JavaScript")
    def execute_script(self, script: str, *args):
        """
        Execute JavaScript on page

        Args:
            script: JavaScript code
            *args: Arguments to pass to script

        Returns:
            Script result
        """
        return self.page.evaluate(script, *args)

    def get_current_url(self) -> str:
        """Get current page URL"""
        return self.page.url

    def get_page_title(self) -> str:
        """Get page title"""
        return self.page.title()

    @allure.step("Press key: {key}")
    def press_key(self, key: str, selector: str = "body"):
        """
        Press keyboard key

        Args:
            key: Key to press (e.g., 'Enter', 'Escape')
            selector: Element selector to focus before pressing
        """
        locator = self.page.locator(selector)
        locator.press(key)
        logger.info(f"Pressed key: {key}")

    @allure.step("Accept alert")
    def accept_alert(self):
        """Accept JavaScript alert/confirm dialog"""
        self.page.once("dialog", lambda dialog: dialog.accept())
        logger.info("Alert accepted")

    @allure.step("Dismiss alert")
    def dismiss_alert(self):
        """Dismiss JavaScript alert/confirm dialog"""
        self.page.once("dialog", lambda dialog: dialog.dismiss())
        logger.info("Alert dismissed")