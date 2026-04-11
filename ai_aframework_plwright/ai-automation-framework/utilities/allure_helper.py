"""
Allure Reporting Helper
Provides per-step log capture, screenshot attachment, and enhanced Allure integration
for Behave BDD tests.
"""

import logging
import io
import allure
from typing import Optional
from playwright.sync_api import Page
from utilities.logger import get_logger

logger = get_logger(__name__)


class StepLogCapture(logging.Handler):
    """
    Custom logging handler that captures log records into a StringIO buffer.
    Used to collect logs generated during a single Behave step,
    then attach them to the Allure report.
    """

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self._buffer = io.StringIO()
        self._formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )

    def emit(self, record):
        try:
            msg = self._formatter.format(record)
            self._buffer.write(msg + "\n")
        except Exception:
            self.handleError(record)

    def get_logs(self) -> str:
        """Return all captured log text."""
        return self._buffer.getvalue()

    def reset(self):
        """Clear the buffer for the next step."""
        self._buffer.truncate(0)
        self._buffer.seek(0)

    def close(self):
        self._buffer.close()
        super().close()


class AllureStepHelper:
    """
    Manages per-step Allure enrichment:
      - Captures logs during each step and attaches them
      - Takes and attaches screenshots on step completion / failure
    """

    def __init__(self):
        self._log_handler: Optional[StepLogCapture] = None
        self._root_logger = logging.getLogger()

    def start_step_logging(self):
        """Attach a fresh StepLogCapture handler to the root logger."""
        self._log_handler = StepLogCapture()
        self._root_logger.addHandler(self._log_handler)

    def stop_step_logging_and_attach(self, step_name: str):
        """
        Remove the capture handler, and attach captured logs to Allure.

        Args:
            step_name: Name of the Behave step (used as attachment title)
        """
        if self._log_handler is None:
            return

        logs = self._log_handler.get_logs()
        self._root_logger.removeHandler(self._log_handler)
        self._log_handler.close()
        self._log_handler = None

        if logs.strip():
            allure.attach(
                logs,
                name=f"Logs: {step_name}",
                attachment_type=allure.attachment_type.TEXT,
            )

    @staticmethod
    def attach_screenshot(page: Page, name: str, full_page: bool = False):
        """
        Take a screenshot and attach it to the current Allure step.

        Args:
            page: Playwright Page instance
            name: Descriptive name for the screenshot
            full_page: Whether to capture the full scrollable page
        """
        try:
            screenshot_bytes = page.screenshot(full_page=full_page)
            allure.attach(
                screenshot_bytes,
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        except Exception as e:
            logger.warning(f"Failed to attach screenshot '{name}': {e}")

    @staticmethod
    def attach_page_source(page: Page, name: str = "Page HTML"):
        """
        Attach current page HTML source to Allure (useful for debugging failures).

        Args:
            page: Playwright Page instance
            name: Attachment name
        """
        try:
            html = page.content()
            allure.attach(
                html,
                name=name,
                attachment_type=allure.attachment_type.HTML,
            )
        except Exception as e:
            logger.warning(f"Failed to attach page source: {e}")
