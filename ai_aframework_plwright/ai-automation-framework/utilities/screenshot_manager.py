"""
Screenshot Manager
Handles screenshot capture and storage
"""

from pathlib import Path
from datetime import datetime
from typing import Dict
from playwright.sync_api import Page
from config.config import config
from utilities.logger import get_logger
from utilities.helpers import sanitize_filename

logger = get_logger(__name__)


class ScreenshotManager:
    """Manages screenshot capture"""

    @staticmethod
    def capture(page: Page, name: str, full_page: bool = False) -> Path:
        """
        Capture screenshot

        Args:
            page: Playwright Page
            name: Screenshot name
            full_page: Capture full page

        Returns:
            Path to screenshot file
        """
        try:
            # Sanitize filename
            safe_name = sanitize_filename(name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}.png"

            # Full path
            screenshot_path = config.screenshots_dir / filename

            # Capture screenshot
            page.screenshot(path=str(screenshot_path), full_page=full_page)

            logger.info(f"Screenshot captured: {screenshot_path}")

            return screenshot_path

        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            raise

    @staticmethod
    def capture_element(page: Page, selector: str, name: str) -> Path:
        """
        Capture element screenshot

        Args:
            page: Playwright Page
            selector: Element selector
            name: Screenshot name

        Returns:
            Path to screenshot file
        """
        try:
            locator = page.locator(selector)

            # Sanitize filename
            safe_name = sanitize_filename(name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_element_{timestamp}.png"

            # Full path
            screenshot_path = config.screenshots_dir / filename

            # Capture element screenshot
            locator.screenshot(path=str(screenshot_path))

            logger.info(f"Element screenshot captured: {screenshot_path}")

            return screenshot_path

        except Exception as e:
            logger.error(f"Failed to capture element screenshot: {str(e)}")
            raise

    @staticmethod
    def compare_screenshots(baseline_path: Path, current_path: Path,
                            threshold: float = 0.1) -> Dict:
        """
        Compare two screenshots

        Args:
            baseline_path: Path to baseline screenshot
            current_path: Path to current screenshot
            threshold: Difference threshold (0-1)

        Returns:
            Comparison result dictionary
        """
        try:
            from PIL import Image
            import numpy as np

            # Load images
            baseline = Image.open(baseline_path)
            current = Image.open(current_path)

            # Convert to numpy arrays
            baseline_arr = np.array(baseline)
            current_arr = np.array(current)

            # Calculate difference
            if baseline_arr.shape != current_arr.shape:
                return {
                    "match": False,
                    "difference": 1.0,
                    "reason": "Different dimensions"
                }

            difference = np.sum(np.abs(baseline_arr - current_arr)) / (
                    baseline_arr.shape[0] * baseline_arr.shape[1] * baseline_arr.shape[2]
            )

            normalized_diff = difference / 255.0

            result = {
                "match": normalized_diff <= threshold,
                "difference": normalized_diff,
                "threshold": threshold
            }

            logger.info(f"Screenshot comparison: difference={normalized_diff:.4f}, match={result['match']}")

            return result

        except Exception as e:
            logger.error(f"Failed to compare screenshots: {str(e)}")
            return {
                "match": False,
                "difference": 1.0,
                "error": str(e)
            }