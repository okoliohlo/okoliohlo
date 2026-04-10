"""
Self-Healing Module — Attribute-Based Healing Strategy
Finds elements by matching stable HTML attributes and their combinations.
"""

import re
from itertools import combinations
from typing import Dict

from playwright.sync_api import Page
from ai.self_healing.strategies.base import BaseHealingStrategy
from ai.self_healing.schemas import ElementMetadata, HealingStrategyResult
from utilities.logger import get_logger

logger = get_logger(__name__)

# Attributes ordered by stability — most reliable first
_PRIORITY_ATTRS = (
    "data-testid", "data-test", "test-id",
    "aria-label", "name", "placeholder",
    "type", "role", "title", "alt",
)

_DYNAMIC_VALUE_RE = re.compile(r"(uuid|guid|timestamp|\d{10,})", re.IGNORECASE)
_DYNAMIC_ID_RE = re.compile(r"\d{4,}")
_UNSTABLE_ATTRS = frozenset({"style", "class"})


class AttributeBasedHealing(BaseHealingStrategy):
    """Locate elements by matching known HTML attributes."""

    def __init__(self, page: Page):
        super().__init__(page, name="Attribute-Based Healing", priority=20)

    def heal(self, metadata: ElementMetadata) -> HealingStrategyResult:
        attributes = metadata.attributes
        if not attributes:
            return HealingStrategyResult(success=False)

        # 1. Single priority attribute
        for attr_name in _PRIORITY_ATTRS:
            attr_value = attributes.get(attr_name)
            if not attr_value:
                continue
            try:
                selector = f"[{attr_name}='{attr_value}']"
                locator = self.page.locator(selector)
                if locator.count() == 1:
                    logger.debug(f"[{self.name}] Matched {attr_name}={attr_value}")
                    return HealingStrategyResult(
                        success=True, locator=locator,
                        new_selector=selector,
                        strategy_name=self.name, confidence=0.92,
                    )
            except Exception as e:
                logger.debug(f"[{self.name}] {attr_name} failed: {e}")

        # 2. Attribute combinations (2-3 stable attrs, optionally with tag)
        result = self._try_combinations(attributes, metadata.tag_name)
        if result.success:
            return result

        return HealingStrategyResult(success=False)

    # ------------------------------------------------------------------

    def _try_combinations(self, attributes: Dict, tag_name: str) -> HealingStrategyResult:
        stable = {
            k: v for k, v in attributes.items()
            if self._is_stable(k, v)
        }
        if not stable:
            return HealingStrategyResult(success=False)

        items = list(stable.items())
        for size in range(min(3, len(items)), 0, -1):
            for combo in combinations(items, size):
                try:
                    parts = [tag_name] if tag_name else []
                    parts.extend(f"[{k}='{v}']" for k, v in combo)
                    selector = "".join(parts)
                    locator = self.page.locator(selector)
                    if locator.count() == 1:
                        confidence = 0.80 + 0.03 * size
                        logger.debug(f"[{self.name}] Combo matched: {selector}")
                        return HealingStrategyResult(
                            success=True, locator=locator,
                            new_selector=selector,
                            strategy_name=self.name, confidence=confidence,
                        )
                except Exception:
                    continue

        return HealingStrategyResult(success=False)

    @staticmethod
    def _is_stable(name: str, value: str) -> bool:
        if name in _UNSTABLE_ATTRS:
            return False
        if name == "id" and _DYNAMIC_ID_RE.search(value):
            return False
        if _DYNAMIC_VALUE_RE.search(value):
            return False
        return True
