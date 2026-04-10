"""
Self-Healing Module — AI-Based Healing Strategy
Uses page DOM analysis and element scoring to predict the most likely
matching element when simpler strategies fail.
"""

import re
from typing import Dict, List, Tuple

from playwright.sync_api import Page
from ai.self_healing.strategies.base import BaseHealingStrategy
from ai.self_healing.schemas import ElementMetadata, HealingStrategyResult
from utilities.logger import get_logger

logger = get_logger(__name__)


class AIBasedHealing(BaseHealingStrategy):
    """
    DOM-analysis healing strategy.

    Instead of relying on a placeholder ML model, this strategy:
    1. Queries all candidate elements from the page that share the same tag.
    2. Scores each candidate against the stored metadata using a weighted
       feature comparison (tag, text, attributes, classes, position).
    3. Returns the highest-scoring unique match above the confidence threshold.

    This is fully deterministic — no randomness.
    """

    CONFIDENCE_THRESHOLD = 0.55

    # Feature weights (sum = 1.0)
    W_TAG = 0.10
    W_TEXT = 0.30
    W_ATTRS = 0.30
    W_CLASSES = 0.15
    W_POSITION = 0.15

    def __init__(self, page: Page):
        super().__init__(page, name="AI-Based Healing", priority=30)

    def heal(self, metadata: ElementMetadata) -> HealingStrategyResult:
        logger.info(f"[{self.name}] Analyzing DOM for '{metadata.name}'")

        try:
            candidates = self._collect_candidates(metadata)
            if not candidates:
                logger.debug(f"[{self.name}] No candidates found")
                return HealingStrategyResult(success=False)

            scored: List[Tuple[int, float, str]] = []
            for idx, candidate in enumerate(candidates):
                score = self._score_candidate(candidate, metadata)
                selector = candidate.get("_selector", "")
                scored.append((idx, score, selector))

            scored.sort(key=lambda t: t[1], reverse=True)
            best_idx, best_score, best_selector = scored[0]

            logger.debug(f"[{self.name}] Best score={best_score:.3f} selector='{best_selector}'")

            if best_score < self.CONFIDENCE_THRESHOLD:
                logger.info(f"[{self.name}] Best score {best_score:.3f} below threshold")
                return HealingStrategyResult(success=False)

            # Verify uniqueness on page
            locator = self.page.locator(best_selector)
            if locator.count() != 1:
                logger.debug(f"[{self.name}] Selector not unique ({locator.count()} matches)")
                return HealingStrategyResult(success=False)

            return HealingStrategyResult(
                success=True,
                locator=locator,
                new_selector=best_selector,
                strategy_name=self.name,
                confidence=round(best_score, 4),
            )

        except Exception as e:
            logger.debug(f"[{self.name}] Exception: {e}")
            return HealingStrategyResult(success=False)

    # ------------------------------------------------------------------
    # Candidate collection
    # ------------------------------------------------------------------

    def _collect_candidates(self, metadata: ElementMetadata) -> List[Dict]:
        """Query the DOM for plausible candidate elements."""
        tag = metadata.tag_name or "*"
        js_script = """
            (tag) => {
                const elems = document.querySelectorAll(tag);
                const results = [];
                for (const el of elems) {
                    const attrs = {};
                    for (const a of el.attributes) {
                        attrs[a.name] = a.value;
                    }
                    const box = el.getBoundingClientRect();
                    results.push({
                        tag: el.tagName.toLowerCase(),
                        text: (el.textContent || '').trim().substring(0, 200),
                        attributes: attrs,
                        classes: Array.from(el.classList),
                        position: {x: box.x, y: box.y, width: box.width, height: box.height},
                    });
                    if (results.length >= 200) break;
                }
                return results;
            }
        """
        candidates = self.page.evaluate(js_script, tag)

        # Attach a reconstructed selector to each candidate
        for c in candidates:
            c["_selector"] = self._build_selector(c)

        return candidates

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_candidate(self, candidate: Dict, metadata: ElementMetadata) -> float:
        score = 0.0
        score += self.W_TAG * self._score_tag(candidate, metadata)
        score += self.W_TEXT * self._score_text(candidate, metadata)
        score += self.W_ATTRS * self._score_attrs(candidate, metadata)
        score += self.W_CLASSES * self._score_classes(candidate, metadata)
        score += self.W_POSITION * self._score_position(candidate, metadata)
        return score

    @staticmethod
    def _score_tag(candidate: Dict, metadata: ElementMetadata) -> float:
        if not metadata.tag_name:
            return 0.5
        return 1.0 if candidate.get("tag") == metadata.tag_name.lower() else 0.0

    @staticmethod
    def _score_text(candidate: Dict, metadata: ElementMetadata) -> float:
        expected = (metadata.text or "").strip()
        actual = (candidate.get("text") or "").strip()
        if not expected:
            return 0.5
        if actual == expected:
            return 1.0
        if expected in actual or actual in expected:
            shorter, longer = sorted([expected, actual], key=len)
            return len(shorter) / len(longer) if longer else 0.0
        return 0.0

    @staticmethod
    def _score_attrs(candidate: Dict, metadata: ElementMetadata) -> float:
        expected = metadata.attributes or {}
        actual = candidate.get("attributes") or {}
        if not expected:
            return 0.5

        stable_keys = [
            "data-testid", "data-test", "test-id",
            "aria-label", "name", "placeholder", "role", "title",
        ]
        checked = 0
        matched = 0
        for key in stable_keys:
            if key in expected:
                checked += 1
                if expected[key] == actual.get(key):
                    matched += 1

        if checked == 0:
            return 0.5
        return matched / checked

    @staticmethod
    def _score_classes(candidate: Dict, metadata: ElementMetadata) -> float:
        expected = set(metadata.css_classes or [])
        actual = set(candidate.get("classes") or [])
        if not expected:
            return 0.5
        union = expected | actual
        if not union:
            return 0.5
        return len(expected & actual) / len(union)

    @staticmethod
    def _score_position(candidate: Dict, metadata: ElementMetadata) -> float:
        expected = metadata.position or {}
        actual = candidate.get("position") or {}
        if not expected or "x" not in expected:
            return 0.5
        try:
            dx = abs(actual.get("x", 0) - expected.get("x", 0))
            dy = abs(actual.get("y", 0) - expected.get("y", 0))
            distance = (dx ** 2 + dy ** 2) ** 0.5
            # Score decays linearly: 0 pixels = 1.0, >=300 pixels = 0.0
            return max(0.0, 1.0 - distance / 300.0)
        except (TypeError, ValueError):
            return 0.5

    # ------------------------------------------------------------------
    # Selector reconstruction
    # ------------------------------------------------------------------

    @staticmethod
    def _build_selector(candidate: Dict) -> str:
        """Build the most specific CSS selector we can for a candidate."""
        attrs = candidate.get("attributes") or {}
        tag = candidate.get("tag", "")

        # Priority 1: data-testid / data-test
        for attr in ("data-testid", "data-test", "test-id"):
            if attr in attrs:
                return f"[{attr}='{attrs[attr]}']"

        # Priority 2: stable id
        eid = attrs.get("id", "")
        if eid and not re.search(r"\d{4,}", eid):
            return f"#{eid}"

        # Priority 3: name
        if "name" in attrs:
            return f"[name='{attrs['name']}']"

        # Priority 4: aria-label
        if "aria-label" in attrs:
            return f"[aria-label='{attrs['aria-label']}']"

        # Priority 5: tag + class
        classes = candidate.get("classes") or []
        if tag and classes:
            return tag + "." + ".".join(classes)

        # Fallback: tag only
        return tag or "*"
