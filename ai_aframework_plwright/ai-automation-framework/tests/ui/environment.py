"""
Behave environment hooks for UI testing
Manages Playwright browser lifecycle and test context via UITest
"""

import os
import allure
from config.config import config
from utilities.logger import get_logger
from utilities.allure_helper import AllureStepHelper
from core.driver_factory import DriverFactory
from core.base_test import UITest

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
    Initialize browser and page via UITest
    """
    logger.info("=" * 60)
    logger.info(f"Scenario: {scenario.name}")
    logger.info(f"Feature: {scenario.feature.name}")
    logger.info("=" * 60)

    # Create a UITest instance and run its setup (DriverFactory handles everything)
    ui_test = UITest()
    ui_test._setup()

    # Expose UITest artefacts on the behave context
    context.ui_test = ui_test
    context.page = ui_test.page
    context.browser_context = ui_test.context

    logger.info("UITest setup completed for scenario")


def after_scenario(context, scenario):
    """
    Runs after each scenario
    Cleanup via UITest._teardown and capture screenshot on failure
    """
    is_failed = scenario.status == 'failed'
    scenario_name = f"{scenario.feature.name}_{scenario.name}".replace(' ', '_')

    # Extra Allure attachments on failure (page source)
    if is_failed and _allure_helper and hasattr(context, 'page'):
        try:
            _allure_helper.attach_page_source(
                context.page,
                name=f"Page source on failure: {scenario.name}"
            )
        except Exception as e:
            logger.error(f"Failed to attach page source: {e}")

    # Delegate teardown to UITest (handles screenshot, video, context close)
    if hasattr(context, 'ui_test'):
        context.ui_test._teardown(failed=is_failed, test_name=scenario_name)

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
