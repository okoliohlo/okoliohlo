"""
Self-Healing Module — Healing Coordinator
Orchestrates the multi-agent pipeline:
  ClassifierAgent → ReasonerAgent → ExecutorAgent → record outcome.

This is the central brain that drives the deterministic healing process.
"""

import hashlib
import uuid
from typing import Optional, List

from playwright.sync_api import Page

from ai.self_healing.schemas import (
    ElementMetadata, FailureType,
    HealingResult, HealingStrategyResult,
    HealingAttempt, HealingReport,
)
from ai.self_healing.agents.classifier import ClassifierAgent
from ai.self_healing.agents.reasoner import ReasonerAgent
from ai.self_healing.agents.executor import ExecutorAgent
from ai.self_healing.database import HealingDatabase
from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


class HealingCoordinator:
    """
    Multi-agent coordinator for the self-healing pipeline.

    Healing flow
    ------------
    1. **Memory lookup** — check if this failure signature was healed before.
       If a high-success-rate memory exists, try its selector first.
    2. **Classify** — ClassifierAgent determines the failure type.
    3. **Propose** — ReasonerAgent generates ordered repair proposals.
    4. **Execute** — ExecutorAgent tries each proposal in turn.
    5. **Record** — persist the outcome to memory + audit log.
    """

    def __init__(self, page: Page, max_attempts: int = 3, include_ai: bool = True):
        self.page = page
        self.max_attempts = max_attempts

        self.classifier = ClassifierAgent()
        self.reasoner = ReasonerAgent()
        self.executor = ExecutorAgent(page, include_ai=include_ai)
        self.db = HealingDatabase()

    # ------------------------------------------------------------------
    # Public API
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

        Args:
            selector: The original selector that failed.
            element_name: Logical name of the element.
            error_message: Error text from the failure.
            stack_trace: Optional stack trace.

        Returns:
            HealingResult with the healed locator (if successful).
        """
        logger.info("=" * 60)
        logger.info(f"SELF-HEALING ACTIVATED for: {element_name}")
        logger.info(f"Failed selector: {selector}")
        logger.info("=" * 60)

        # Load stored metadata
        metadata = self._load_metadata(element_name, selector)

        attempts: List[HealingAttempt] = []

        # ----- Phase 1: Memory recall -----
        memory_result = self._try_memory(metadata)
        if memory_result and memory_result.success:
            self._record_success(metadata, memory_result, "memory_recall")
            return memory_result

        # ----- Phase 2: Classify -----
        classification = self.classifier.classify(
            error_message=error_message or f"Element not found: {selector}",
            stack_trace=stack_trace,
            metadata=metadata,
        )
        logger.info(f"[Coordinator] Classification: {classification.failure_type.value} "
                     f"(confidence={classification.confidence:.2f})")

        # ----- Phase 3: Propose -----
        proposals = self.reasoner.propose(classification, metadata)

        # ----- Phase 4: Execute proposals -----
        for proposal in proposals[:self.max_attempts]:
            attempt = self.executor.execute(proposal, metadata)
            attempts.append(attempt)

            if attempt.success and attempt.result and attempt.result.locator:
                logger.info(f"[Coordinator] HEALED by {attempt.result.strategy_name}")

                # ----- Phase 5: Record -----
                self._record_success(
                    metadata, 
                    HealingResult(
                        success=True,
                        locator=attempt.result.locator,
                        new_selector=attempt.result.new_selector,
                        strategy=attempt.result.strategy_name,
                        confidence=attempt.confidence,
                        attempts=len(attempts),
                        failure_type=classification.failure_type,
                    ),
                    action="healed",
                )

                return HealingResult(
                    success=True,
                    locator=attempt.result.locator,
                    new_selector=attempt.result.new_selector,
                    strategy=attempt.result.strategy_name,
                    confidence=attempt.confidence,
                    attempts=len(attempts),
                    failure_type=classification.failure_type,
                )

        # All proposals exhausted
        logger.error(f"[Coordinator] All strategies failed for: {element_name}")
        self._record_failure(metadata, attempts)

        return HealingResult(
            success=False,
            attempts=len(attempts),
            failure_type=classification.failure_type,
        )

    # ------------------------------------------------------------------
    # Memory recall
    # ------------------------------------------------------------------

    def _try_memory(self, metadata: ElementMetadata) -> Optional[HealingResult]:
        """Check memory for a previously successful healing."""
        memories = self.db.lookup_memory_by_element(metadata.name)
        if not memories:
            return None

        for mem in memories:
            total = mem.get("success_count", 0) + mem.get("failure_count", 0)
            if total == 0:
                continue
            success_rate = mem["success_count"] / total
            if success_rate < 0.60:
                continue

            healed_selector = mem.get("healed_selector", "")
            if not healed_selector:
                continue

            try:
                locator = self.page.locator(healed_selector)
                locator.wait_for(state="attached", timeout=3000)
                if locator.count() == 1:
                    logger.info(
                        f"[Coordinator] Memory hit: '{healed_selector}' "
                        f"(success_rate={success_rate:.2f})"
                    )
                    # Update usage
                    sig = self._signature(metadata)
                    self.db.store_memory(
                        signature=sig,
                        failure_type=mem.get("failure_type", "LOCATOR_CHANGE"),
                        element_name=metadata.name,
                        original_selector=metadata.selector,
                        healed_selector=healed_selector,
                        strategy=mem.get("strategy", "memory_recall"),
                        confidence=mem.get("confidence", 0.80),
                        success=True,
                    )
                    return HealingResult(
                        success=True,
                        locator=locator,
                        new_selector=healed_selector,
                        strategy="memory_recall",
                        confidence=min(0.95, success_rate),
                        attempts=0,
                    )
            except Exception as e:
                logger.debug(f"[Coordinator] Memory selector failed: {e}")
                continue

        return None

    # ------------------------------------------------------------------
    # Metadata loading
    # ------------------------------------------------------------------

    def _load_metadata(self, element_name: str, selector: str) -> ElementMetadata:
        """Load metadata from DB or create a minimal stub."""
        row = self.db.get_element(element_name)
        if row:
            return ElementMetadata(
                name=row["name"],
                selector=row["selector"],
                tag_name=row.get("tag_name", ""),
                text=row.get("text", ""),
                attributes=row.get("attributes", {}),
                position=row.get("position", {}),
                css_classes=row.get("css_classes", []),
                timestamp=row.get("timestamp", ""),
            )

        logger.warning(f"[Coordinator] No metadata for '{element_name}' — using stub")
        return ElementMetadata(name=element_name, selector=selector)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _record_success(
        self, metadata: ElementMetadata, result: HealingResult, action: str,
    ):
        sig = self._signature(metadata)
        strategy = result.strategy or "unknown"

        # Memory
        self.db.store_memory(
            signature=sig,
            failure_type=result.failure_type.value if result.failure_type else "LOCATOR_CHANGE",
            element_name=metadata.name,
            original_selector=metadata.selector,
            healed_selector=result.new_selector or "",
            strategy=strategy,
            confidence=result.confidence,
            success=True,
        )

        # Selector history
        if result.new_selector and result.new_selector != metadata.selector:
            self.db.record_selector_change(
                element_name=metadata.name,
                old_selector=metadata.selector,
                new_selector=result.new_selector,
                strategy=strategy,
                confidence=result.confidence,
            )

            # Update element metadata with new selector
            self.db.store_element(
                name=metadata.name,
                selector=result.new_selector,
                tag_name=metadata.tag_name,
                text=metadata.text,
                attributes=metadata.attributes,
                position=metadata.position,
                css_classes=metadata.css_classes,
            )

        # Audit
        self.db.write_audit(
            entry_id=uuid.uuid4().hex,
            action=action,
            element_name=metadata.name,
            old_selector=metadata.selector,
            new_selector=result.new_selector or "",
            strategy=strategy,
            confidence=result.confidence,
            success=True,
        )

    def _record_failure(self, metadata: ElementMetadata, attempts: List[HealingAttempt]):
        sig = self._signature(metadata)
        strategies_tried = ", ".join(
            (a.proposal.strategy.value if a.proposal else "unknown") for a in attempts
        )

        self.db.store_memory(
            signature=sig,
            failure_type="UNKNOWN",
            element_name=metadata.name,
            original_selector=metadata.selector,
            healed_selector="",
            strategy=strategies_tried,
            confidence=0.0,
            success=False,
        )

        self.db.write_audit(
            entry_id=uuid.uuid4().hex,
            action="healing_failed",
            element_name=metadata.name,
            old_selector=metadata.selector,
            strategy=strategies_tried,
            confidence=0.0,
            success=False,
            details={"attempts": len(attempts)},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _signature(metadata: ElementMetadata) -> str:
        """Deterministic failure signature based on element name + selector."""
        raw = f"{metadata.name}:{metadata.selector}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]
