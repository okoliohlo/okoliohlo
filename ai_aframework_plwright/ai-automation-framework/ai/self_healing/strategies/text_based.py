"""
Self-Healing Module — Text-Based Healing Strategy
Finds elements by matching visible text content on the live page.
"""

from playwright.sync_api import Page
from ai.self_healing.strategies.base import BaseHealingStrategy
from ai.self_healing.schemas import ElementMetadata, HealingStrategyResult
from utilities.logger import get_logger

logger = get_logger(__name__)


class TextBasedHealing(BaseHealingStrategy):
    """Locate elements by their text content using Playwright text selectors."""

    def __init__(self, page: Page):
        super().__init__(page, name="Text-Based Healing", priority=10)

    def heal(self, metadata: ElementMetadata) -> HealingStrategyResult:
        text = metadata.text
        tag = metadata.tag_name
        logger.info(f"[{self.name}] Searching for text='{text}' tag='{tag}'")

        if not text or not text.strip():
            logger.debug(f"[{self.name}] No text in metadata — skipping")
            return HealingStrategyResult(success=False)

        try:
            # 1. Tag + :has-text() — most specific
            if tag:
                locator = self.page.locator(f"{tag}:has-text('{text}')")
                count = locator.count()
                logger.debug(f"[{self.name}] tag+has-text matched {count}")
                if count == 1:
                    return HealingStrategyResult(
                        success=True, locator=locator,
                        strategy_name=self.name, confidence=0.90,
                    )
                if count > 1:
                    # Narrow to exact text match
                    for i in range(min(count, 10)):
                        elem = locator.nth(i)
                        if (elem.text_content() or "").strip() == text.strip():
                            return HealingStrategyResult(
                                success=True, locator=elem,
                                strategy_name=self.name, confidence=0.88,
                            )

            # 2. get_by_text exact
            locator = self.page.get_by_text(text, exact=True)
            if locator.count() == 1:
                return HealingStrategyResult(
                    success=True, locator=locator,
                    strategy_name=self.name, confidence=0.85,
                )

            # 3. get_by_text partial
            locator = self.page.get_by_text(text)
            if locator.count() == 1:
                return HealingStrategyResult(
                    success=True, locator=locator,
                    strategy_name=self.name, confidence=0.75,
                )

            # 4. get_by_role with name (for buttons / links)
            if tag in ("button", "a", "input"):
                role_map = {"button": "button", "a": "link", "input": "textbox"}
                role = role_map.get(tag)
                if role:
                    locator = self.page.get_by_role(role, name=text)
                    if locator.count() == 1:
                        return HealingStrategyResult(
                            success=True, locator=locator,
                            strategy_name=self.name, confidence=0.82,
                        )

            logger.info(f"[{self.name}] Could not uniquely identify element")

        except Exception as e:
            logger.debug(f"[{self.name}] Exception: {e}")

        return HealingStrategyResult(success=False)