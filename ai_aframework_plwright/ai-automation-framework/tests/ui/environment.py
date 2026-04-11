"""
Behave environment hooks for UI testing
Manages Playwright browser lifecycle and test context
"""

import os
import allure
from playwright.sync_api import sync_playwright
from config.config import config
from utilities.logger import get_logger
from utilities.allure_helper import AllureStepHelper
from core.driver_factory import DriverFactory

logger = get_logger(__name__)

# Shared helper - created once per session in before_all
_allure_helper: AllureStepHelper = None


def before_all(context):
    """
    Runs once before all tests
    Setup global test configuration
    """
    global _allure_helper
    _allure_helper = AllureStepHelper()

    logger.info("=" * 80)
    logger.info("BEHAVE TEST SESSION STARTED")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Base URL: {config.get_base_url()}")
    logger.info(f"Browser: {config.env_config.browser}")
    logger.info(f"Headless: {config.env_config.headless}")
    logger.info("=" * 80)
    
    # Store config in context
    context.config.userdata.setdefault('browser', config.env_config.browser)
    context.config.userdata.setdefault('headless', str(config.env_config.headless))
    context.config.userdata.setdefault('base_url', config.get_base_url())


def before_scenario(context, scenario):
    """
    Runs before each scenario
    Initialize browser and page for the scenario
    """
    logger.info("=" * 60)
    logger.info(f"Scenario: {scenario.name}")
    logger.info(f"Feature: {scenario.feature.name}")
    logger.info("=" * 60)
    
    # Get browser configuration from centralized config
    browser_config = config.get_browser_config()
    browser_type = context.config.userdata.get('browser', browser_config['browser_type'])
    headless = context.config.userdata.get('headless', str(browser_config['headless'])).lower() == 'true'
    
    # Initialize Playwright browser and page
    context.playwright = sync_playwright().start()
    
    # Launch browser
    if browser_type.lower() == 'chromium':
        context.browser = context.playwright.chromium.launch(headless=headless)
    elif browser_type.lower() == 'firefox':
        context.browser = context.playwright.firefox.launch(headless=headless)
    elif browser_type.lower() == 'webkit':
        context.browser = context.playwright.webkit.launch(headless=headless)
    else:
        context.browser = context.playwright.chromium.launch(headless=headless)
    
    # Create browser context with viewport from centralized config
    context.browser_context = context.browser.new_context(
        viewport={
            'width': config.env_config.viewport_width,
            'height': config.env_config.viewport_height
        },
        ignore_https_errors=True
    )
    
    # Create page with self-healing support using DriverFactory
    context.page = DriverFactory.create_page(context.browser_context)
    
    # Set default timeout from centralized config
    context.page.set_default_timeout(config.env_config.timeout)
    
    logger.info(f"Browser initialized: {browser_type} (headless={headless})")
    logger.info(f"Viewport: {config.env_config.viewport_width}x{config.env_config.viewport_height}")
    logger.info(f"Timeout: {config.env_config.timeout}ms")


def after_scenario(context, scenario):
    """
    Runs after each scenario
    Cleanup browser and capture screenshot on failure
    """
    # Capture screenshot on failure
    if scenario.status == 'failed':
        try:
            # Use centralized config for screenshot directory
            screenshot_dir = str(config.screenshots_dir)
            os.makedirs(screenshot_dir, exist_ok=True)
            
            screenshot_name = f"{scenario.feature.name}_{scenario.name}".replace(' ', '_')
            screenshot_path = os.path.join(screenshot_dir, f"{screenshot_name}_failed.png")
            
            context.page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Screenshot saved: {screenshot_path}")
            
            # Attach full-page screenshot to Allure
            allure.attach.file(
                screenshot_path,
                name=f"FAILED: {scenario.name} (full page)",
                attachment_type=allure.attachment_type.PNG
            )
            
            # Attach page HTML source for debugging
            if _allure_helper and hasattr(context, 'page'):
                _allure_helper.attach_page_source(
                    context.page,
                    name=f"Page source on failure: {scenario.name}"
                )
                
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {e}")
    
    # Close browser
    try:
        if hasattr(context, 'page'):
            context.page.close()
        if hasattr(context, 'browser_context'):
            context.browser_context.close()
        if hasattr(context, 'browser'):
            context.browser.close()
        if hasattr(context, 'playwright'):
            context.playwright.stop()
    except Exception as e:
        logger.error(f"Error during browser cleanup: {e}")
    
    logger.info(f"Scenario completed: {str(scenario.status).upper()}")


def after_all(context):
    """
    Runs once after all tests
    Final cleanup
    """
    logger.info("=" * 80)
    logger.info("BEHAVE TEST SESSION COMPLETED")
    logger.info("=" * 80)
    
    # Cleanup DriverFactory if needed
    try:
        DriverFactory.cleanup()
    except Exception:
        pass


def before_step(context, step):
    """
    Runs before each step
    Starts per-step log capture for Allure attachment
    """
    logger.debug(f"Step: {step.keyword} {step.name}")
    if _allure_helper:
        _allure_helper.start_step_logging()


def after_step(context, step):
    """
    Runs after each step
    Attaches captured logs and screenshots to Allure report
    """
    step_title = f"{step.keyword} {step.name}"

    # 1. Attach captured logs for this step
    if _allure_helper:
        _allure_helper.stop_step_logging_and_attach(step_title)

    # 2. Handle screenshots
    if hasattr(context, 'page'):
        if step.status == 'failed':
            logger.error(f"Step FAILED: {step_title}")
            # Screenshot on failure - always full page
            if _allure_helper:
                _allure_helper.attach_screenshot(
                    context.page,
                    name=f"FAILED: {step_title}",
                    full_page=True,
                )
        else:
            # Screenshot on success - lightweight viewport only
            if _allure_helper:
                _allure_helper.attach_screenshot(
                    context.page,
                    name=f"Step: {step_title}",
                    full_page=False,
                )
