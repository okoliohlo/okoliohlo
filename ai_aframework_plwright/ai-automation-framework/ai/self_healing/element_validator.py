"""
Self-Healing Module — Element Validator
Validates that a healed element matches the expected characteristics
stored in ElementMetadata.  Returns a deterministic confidence score.
"""

from playwright.sync_api import Locator
from ai.self_healing.schemas import ElementMetadata
from utilities.logger import get_logger

logger = get_logger(__name__)


class ElementValidator:
    """
    Multi-check validator for healed elements.

    Checks (in order):
      1. Tag name
      2. Text content
      3. Key attributes (data-testid, aria-label, etc.)
      4. Visibility / attached state

    Each check contributes to a weighted confidence score.
    The validator passes if total confidence >= threshold.
    """

    # Weights (sum = 1.0)
    W_TAG = 0.20
    W_TEXT = 0.30
    W_ATTRS = 0.35
    W_VISIBLE = 0.15

    DEFAULT_THRESHOLD = 0.50

    _INTERACTIVE_TAGS = frozenset({"button", "a", "input", "select", "textarea"})
    _CRITICAL_ATTRS = ("data-testid", "data-test", "aria-label", "name", "role")

    def __init__(self, threshold: float = None):
        self.threshold = threshold or self.DEFAULT_THRESHOLD

    def validate(self, locator: Locator, metadata: ElementMetadata) -> bool:
        """
        Validate the locator against stored metadata.

        Returns:
            True if overall confidence >= threshold.
        """
        try:
            score = self.score(locator, metadata)
            passed = score >= self.threshold
            logger.info(
                f"[Validator] score={score:.2f} threshold={self.threshold:.2f} "
                f"result={'PASS' if passed else 'FAIL'}"
            )
            return passed
        except Exception as e:
            logger.warning(f"[Validator] Exception during validation: {e}")
            return False

    def score(self, locator: Locator, metadata: ElementMetadata) -> float:
        """
        Calculate a weighted confidence score (0.0 – 1.0).
        """
        total = 0.0
        total += self.W_TAG * self._score_tag(locator, metadata)
        total += self.W_TEXT * self._score_text(locator, metadata)
        total += self.W_ATTRS * self._score_attrs(locator, metadata)
        total += self.W_VISIBLE * self._score_visible(locator)
        return round(total, 4)

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _score_tag(self, locator: Locator, metadata: ElementMetadata) -> float:
        if not metadata.tag_name:
            return 1.0  # No constraint → pass

        try:
            actual = locator.first.evaluate("el => el.tagName.toLowerCase()")
            expected = metadata.tag_name.lower()

            if actual == expected:
                return 1.0

            # Allow interactive-tag interchange (button ↔ a, etc.)
            if actual in self._INTERACTIVE_TAGS and expected in self._INTERACTIVE_TAGS:
                logger.debug(f"[Validator] Tag soft-match: {actual} ~ {expected}")
                return 0.7

            logger.debug(f"[Validator] Tag mismatch: {actual} != {expected}")
            return 0.0
        except Exception:
            return 0.5  # Cannot evaluate → neutral

    def _score_text(self, locator: Locator, metadata: ElementMetadata) -> float:
        if not metadata.text:
            return 1.0

        try:
            actual = (locator.text_content() or "").strip()
            expected = metadata.text.strip()

            if actual == expected:
                return 1.0
            if expected in actual or actual in expected:
                shorter, longer = sorted([expected, actual], key=len)
                return len(shorter) / len(longer) if longer else 0.0
            return 0.0
        except Exception:
            return 0.0

    def _score_attrs(self, locator: Locator, metadata: ElementMetadata) -> float:
        if not metadata.attributes:
            return 1.0

        checked = 0
        matched = 0
        for attr in self._CRITICAL_ATTRS:
            expected_val = metadata.attributes.get(attr)
            if expected_val is None:
                continue
            checked += 1
            try:
                actual_val = locator.get_attribute(attr)
                if actual_val == expected_val:
                    matched += 1
            except Exception:
                pass

        if checked == 0:
            return 1.0
        return matched / checked

    @staticmethod
    def _score_visible(locator: Locator) -> float:
        try:
            if locator.is_visible():
                return 1.0
            if locator.is_enabled():
                return 0.5
            return 0.0
        except Exception:
            return 0.3
