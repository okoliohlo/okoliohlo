"""
Self-Healing Module — Healing Engine
Main entry point that integrates with Playwright via DriverFactory.

Backward-compatible API:
    engine = HealingEngine(page)
    engine.record_success(element_name, selector, locator)
    result = engine.heal(selector, element_name)
"""

import re
from typing import Optional, Dict, Any

from playwright.sync_api import Page, Locator

from ai.self_healing.schemas import (
    ElementMetadata, HealingResult, HealingReport,
)
from ai.self_healing.agents.coordinator import HealingCoordinator
from ai.self_healing.database import HealingDatabase
from ai.self_healing.element_validator import ElementValidator
from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


class HealingEngine:
    """
    Core self-healing engine — facade that DriverFactory calls.

    Responsibilities:
      - Record successful element interactions (metadata snapshots).
      - Attempt healing when a selector fails.
      - Expose statistics and history for reporting.
    """

    def __init__(self, page: Page):
        """
        Initialize healing engine.

        Args:
            page: Playwright Page instance.
        """
        self.page = page
        self.db = HealingDatabase()
        self.validator = ElementValidator()
        self.coordinator = HealingCoordinator(
            page,
            max_attempts=3,
            include_ai=config.ai_analysis_enabled,
        )

        logger.info("HealingEngine initialized (unified multi-agent pipeline)")

    # ------------------------------------------------------------------
    # Record element metadata on successful interaction
    # ------------------------------------------------------------------

    def record_success(self, element_name: str, selector: str, locator: Locator):
        """
        Record a successful element location for future healing.

        Args:
            element_name: Logical name of the element.
            selector: Selector that was used.
            locator: Playwright Locator that resolved successfully.
        """
        try:
            locator.wait_for(state="attached", timeout=5000)
            element = locator.element_handle(timeout=5000)
            if element is None:
                return

            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            text = (locator.text_content() or "").strip()[:500]
            attributes = element.evaluate("""
                el => {
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            """)
            position = locator.bounding_box() or {}
            css_classes = element.evaluate("el => Array.from(el.classList)")

            self.db.store_element(
                name=element_name,
                selector=selector,
                tag_name=tag_name,
                text=text,
                attributes=attributes,
                position=position,
                css_classes=css_classes,
            )
            logger.debug(
                f"[Engine] Recorded metadata: {element_name} | "
                f"selector='{selector}' | text='{text[:50]}'"
            )

        except Exception as e:
            logger.warning(f"[Engine] Failed to record metadata for {element_name}: {e}")

    # ------------------------------------------------------------------
    # Heal a failed selector
    # ------------------------------------------------------------------

    def heal(
        self,
        selector: str,
        element_name: str,
        error_message: str = "",
        stack_trace: str = "",
    ) -> HealingResult:
        """
        Attempt to heal a failed element location.

        This is the main entry point called by DriverFactory when
        a locator fails.

        Args:
            selector: The original selector that failed.
            element_name: Logical name of the element.
            error_message: Error text from the failure.
            stack_trace: Optional stack trace.

        Returns:
            HealingResult with success flag and optional healed locator.
        """
        result = self.coordinator.heal(
            selector=selector,
            element_name=element_name,
            error_message=error_message,
            stack_trace=stack_trace,
        )

        if result.success:
            self._notify_healing(element_name, selector, result)

        return result

    # ------------------------------------------------------------------
    # Statistics & history
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return aggregate healing statistics."""
        return {
            "memory": self.db.get_memory_stats(),
            "audit": self.db.get_audit_stats(),
        }

    def get_element_history(self, element_name: str) -> Dict[str, Any]:
        """Return selector history and audit log for one element."""
        return {
            "selector_history": self.db.get_selector_history(element_name),
            "audit_log": self.db.get_audit_log(element_name),
            "memory": self.db.lookup_memory_by_element(element_name),
        }

    # ------------------------------------------------------------------
    # Notification
    # ------------------------------------------------------------------

    @staticmethod
    def _notify_healing(element_name: str, old_selector: str, result: HealingResult):
        """Log a human-readable healing notification."""
        msg = (
            f"\n{'=' * 50}\n"
            f"SELF-HEALING SUCCESSFUL\n"
            f"  Element:      {element_name}\n"
            f"  Old selector: {old_selector}\n"
            f"  New selector: {result.new_selector}\n"
            f"  Strategy:     {result.strategy}\n"
            f"  Confidence:   {result.confidence:.2f}\n"
            f"  Attempts:     {result.attempts}\n"
            f"  Environment:  {config.environment}\n"
            f"{'=' * 50}"
        )
        logger.info(msg)
