"""
Self-Healing Module — Executor Agent
Executes repair proposals at runtime against a live Playwright page.
Handles strategy dispatch, selector discovery, and element validation.
"""

import re
import uuid
from typing import List, Optional

from playwright.sync_api import Page, Locator

from ai.self_healing.schemas import (
    ElementMetadata, HealingStrategyResult, RepairProposal,
    RepairStrategy, HealingAttempt,
)
from ai.self_healing.element_validator import ElementValidator
from ai.self_healing.strategies import build_strategy_chain, BaseHealingStrategy
from ai.self_healing.database import HealingDatabase
from utilities.logger import get_logger

logger = get_logger(__name__)


class ExecutorAgent:
    """
    Runs repair proposals against the live page.

    For locator-based strategies it delegates to the strategy chain.
    For non-locator strategies (wait increase, retry) it returns
    metadata so the caller can act accordingly.
    """

    def __init__(self, page: Page, include_ai: bool = True):
        self.page = page
        self.validator = ElementValidator()
        self.strategies: List[BaseHealingStrategy] = build_strategy_chain(page, include_ai)
        self.db = HealingDatabase()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        proposal: RepairProposal,
        metadata: ElementMetadata,
    ) -> HealingAttempt:
        """
        Execute a single RepairProposal.

        Returns a HealingAttempt record with the outcome.
        """
        attempt_id = uuid.uuid4().hex[:8]

        if proposal.strategy in (
            RepairStrategy.TEXT_BASED,
            RepairStrategy.ATTRIBUTE_BASED,
            RepairStrategy.AI_BASED,
            RepairStrategy.SELECTOR_FALLBACK,
        ):
            return self._execute_locator_strategy(attempt_id, proposal, metadata)

        if proposal.strategy == RepairStrategy.INCREASE_WAIT:
            return self._execute_increase_wait(attempt_id, proposal, metadata)

        if proposal.strategy == RepairStrategy.RETRY:
            return self._execute_retry(attempt_id, proposal, metadata)

        # MANUAL_REVIEW or unknown
        return HealingAttempt(
            attempt_id=attempt_id,
            element_name=metadata.name,
            original_selector=metadata.selector,
            proposal=proposal,
            success=False,
            confidence=0.0,
        )

    # ------------------------------------------------------------------
    # Locator healing
    # ------------------------------------------------------------------

    def _execute_locator_strategy(
        self,
        attempt_id: str,
        proposal: RepairProposal,
        metadata: ElementMetadata,
    ) -> HealingAttempt:
        """Try each strategy in the chain until one succeeds validation."""
        target_strategies = self._filter_strategies(proposal.strategy)

        for strategy in target_strategies:
            logger.debug(f"[Executor] Trying {strategy.name}")
            try:
                result = strategy.heal(metadata)

                if not result.success or result.locator is None:
                    continue

                # Validate
                if not self.validator.validate(result.locator, metadata):
                    logger.debug(f"[Executor] {strategy.name} failed validation")
                    continue

                # Discover optimal selector for the healed element
                new_selector = result.new_selector or self._discover_selector(result.locator)

                logger.info(
                    f"[Executor] Healed by {strategy.name} -> '{new_selector}' "
                    f"(confidence={result.confidence:.2f})"
                )

                return HealingAttempt(
                    attempt_id=attempt_id,
                    element_name=metadata.name,
                    original_selector=metadata.selector,
                    proposal=proposal,
                    result=HealingStrategyResult(
                        success=True,
                        locator=result.locator,
                        new_selector=new_selector,
                        strategy_name=strategy.name,
                        confidence=result.confidence,
                    ),
                    success=True,
                    confidence=result.confidence,
                )

            except Exception as e:
                logger.debug(f"[Executor] {strategy.name} exception: {e}")
                continue

        return HealingAttempt(
            attempt_id=attempt_id,
            element_name=metadata.name,
            original_selector=metadata.selector,
            proposal=proposal,
            success=False,
            confidence=0.0,
        )

    def _filter_strategies(self, target: RepairStrategy) -> List[BaseHealingStrategy]:
        """
        If the proposal targets a specific strategy, try it first
        then fall through to the rest of the chain.
        """
        name_map = {
            RepairStrategy.TEXT_BASED: "Text-Based Healing",
            RepairStrategy.ATTRIBUTE_BASED: "Attribute-Based Healing",
            RepairStrategy.AI_BASED: "AI-Based Healing",
        }
        preferred = name_map.get(target)
        if not preferred:
            return list(self.strategies)

        ordered = sorted(
            self.strategies,
            key=lambda s: (0 if s.name == preferred else 1, s.priority),
        )
        return ordered

    # ------------------------------------------------------------------
    # Non-locator strategies
    # ------------------------------------------------------------------

    def _execute_increase_wait(
        self, attempt_id: str, proposal: RepairProposal, metadata: ElementMetadata,
    ) -> HealingAttempt:
        """Increase page default timeout and retry the locator."""
        multiplier = proposal.proposed_changes.get("multiplier", 1.5)
        current_timeout = self.page.context.browser.contexts[0]._timeout if hasattr(self.page, 'context') else 30000

        try:
            new_timeout = int(current_timeout * multiplier)
            self.page.set_default_timeout(new_timeout)
            logger.info(f"[Executor] Timeout increased to {new_timeout}ms")

            locator = self.page.locator(metadata.selector)
            locator.wait_for(state="attached", timeout=new_timeout)

            if locator.count() >= 1:
                return HealingAttempt(
                    attempt_id=attempt_id,
                    element_name=metadata.name,
                    original_selector=metadata.selector,
                    proposal=proposal,
                    result=HealingStrategyResult(
                        success=True, locator=locator,
                        new_selector=metadata.selector,
                        strategy_name="Increase Wait",
                        confidence=0.70,
                    ),
                    success=True,
                    confidence=0.70,
                )
        except Exception as e:
            logger.debug(f"[Executor] Increase wait failed: {e}")

        return HealingAttempt(
            attempt_id=attempt_id,
            element_name=metadata.name,
            original_selector=metadata.selector,
            proposal=proposal,
            success=False,
            confidence=0.0,
        )

    def _execute_retry(
        self, attempt_id: str, proposal: RepairProposal, metadata: ElementMetadata,
    ) -> HealingAttempt:
        """Retry the original selector with back-off pauses."""
        import time

        backoffs = proposal.proposed_changes.get("backoff_seconds", [1, 2, 4])

        for wait in backoffs:
            try:
                time.sleep(wait)
                locator = self.page.locator(metadata.selector)
                locator.wait_for(state="attached", timeout=5000)
                if locator.count() >= 1:
                    logger.info(f"[Executor] Retry succeeded after {wait}s wait")
                    return HealingAttempt(
                        attempt_id=attempt_id,
                        element_name=metadata.name,
                        original_selector=metadata.selector,
                        proposal=proposal,
                        result=HealingStrategyResult(
                            success=True, locator=locator,
                            new_selector=metadata.selector,
                            strategy_name="Retry",
                            confidence=0.60,
                        ),
                        success=True,
                        confidence=0.60,
                    )
            except Exception:
                continue

        return HealingAttempt(
            attempt_id=attempt_id,
            element_name=metadata.name,
            original_selector=metadata.selector,
            proposal=proposal,
            success=False,
            confidence=0.0,
        )

    # ------------------------------------------------------------------
    # Selector discovery
    # ------------------------------------------------------------------

    def _discover_selector(self, locator: Locator) -> str:
        """Build the best possible selector for a healed element."""
        try:
            element = locator.element_handle(timeout=3000)
            if element is None:
                return ""

            # 1. Stable ID
            eid = element.evaluate("el => el.id")
            if eid and not re.search(r"\d{4,}", eid):
                return f"#{eid}"

            # 2. data-test* attributes
            for attr in ("data-testid", "data-test", "test-id"):
                val = element.evaluate(f"el => el.getAttribute('{attr}')")
                if val:
                    return f"[{attr}='{val}']"

            # 3. name attribute
            name = element.evaluate("el => el.getAttribute('name')")
            if name:
                return f"[name='{name}']"

            # 4. aria-label
            aria = element.evaluate("el => el.getAttribute('aria-label')")
            if aria:
                return f"[aria-label='{aria}']"

            # 5. Unique class combination
            tag = element.evaluate("el => el.tagName.toLowerCase()")
            classes = element.evaluate("el => el.className")
            class_part = "." + ".".join(classes.split()) if classes else ""

            if class_part:
                selector = class_part
                if self.page.locator(selector).count() == 1:
                    return selector

            # 6. Tag + classes
            if tag and class_part:
                selector = f"{tag}{class_part}"
                if self.page.locator(selector).count() == 1:
                    return selector

            # 7. Classes/tag + href (critical for links)
            href = element.evaluate("el => el.getAttribute('href')")
            if href:
                for base in [f"{tag}{class_part}", class_part, tag]:
                    if not base:
                        continue
                    selector = f"{base}[href='{href}']"
                    if self.page.locator(selector).count() == 1:
                        return selector

            # 8. Classes/tag + type, role, or placeholder
            for attr in ("type", "role", "placeholder"):
                val = element.evaluate(f"el => el.getAttribute('{attr}')")
                if val:
                    for base in [f"{tag}{class_part}", class_part, tag]:
                        if not base:
                            continue
                        selector = f"{base}[{attr}='{val}']"
                        if self.page.locator(selector).count() == 1:
                            return selector

            # 9. XPath fallback
            xpath = element.evaluate("""
                el => {
                    const parts = [];
                    let current = el;
                    while (current && current.nodeType === 1) {
                        let tag = current.tagName.toLowerCase();
                        let sibling = current;
                        let idx = 1;
                        while (sibling.previousElementSibling) {
                            sibling = sibling.previousElementSibling;
                            if (sibling.tagName === current.tagName) idx++;
                        }
                        parts.unshift(tag + '[' + idx + ']');
                        current = current.parentNode;
                        if (current === document.body) { parts.unshift('body'); break; }
                    }
                    return '/' + parts.join('/');
                }
            """)
            return xpath or ""

        except Exception as e:
            logger.debug(f"[Executor] Selector discovery failed: {e}")
            return ""
