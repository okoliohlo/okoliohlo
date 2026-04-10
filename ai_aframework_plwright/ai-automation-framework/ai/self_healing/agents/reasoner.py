"""
Self-Healing Module — Reasoner Agent
Generates deterministic repair proposals based on failure classification
and stored element metadata.  No LLM or randomness.
"""

from typing import List

from ai.self_healing.schemas import (
    FailureType, FailureClassification, RepairProposal, RepairStrategy,
    ElementMetadata,
)
from utilities.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Strategy mapping — each FailureType maps to an ordered list of strategies
# with deterministic confidence values.
# ---------------------------------------------------------------------------

_STRATEGY_MAP = {
    FailureType.LOCATOR_CHANGE: [
        (RepairStrategy.TEXT_BASED, 0.90, "LOW",
         "Attempt text-based element relocation"),
        (RepairStrategy.ATTRIBUTE_BASED, 0.85, "LOW",
         "Attempt attribute-based element relocation"),
        (RepairStrategy.AI_BASED, 0.75, "LOW",
         "Attempt AI/DOM-analysis element relocation"),
        (RepairStrategy.SELECTOR_FALLBACK, 0.60, "MEDIUM",
         "Generate alternative CSS/XPath selectors"),
    ],
    FailureType.TIMING_ISSUE: [
        (RepairStrategy.INCREASE_WAIT, 0.80, "LOW",
         "Increase wait/timeout by 50%"),
        (RepairStrategy.RETRY, 0.70, "LOW",
         "Retry with exponential backoff"),
    ],
    FailureType.API_SCHEMA_CHANGE: [
        (RepairStrategy.MANUAL_REVIEW, 0.40, "HIGH",
         "API schema change requires manual review"),
    ],
    FailureType.ENVIRONMENT: [
        (RepairStrategy.RETRY, 0.65, "LOW",
         "Retry — environment may recover"),
        (RepairStrategy.MANUAL_REVIEW, 0.30, "MEDIUM",
         "Environment issue — escalate if retry fails"),
    ],
    FailureType.DATA_ISSUE: [
        (RepairStrategy.MANUAL_REVIEW, 0.35, "MEDIUM",
         "Data assertion mismatch — manual verification needed"),
    ],
    FailureType.UNKNOWN: [
        (RepairStrategy.RETRY, 0.30, "LOW",
         "Unknown failure — retry as first attempt"),
        (RepairStrategy.MANUAL_REVIEW, 0.20, "HIGH",
         "Unknown failure — escalate for review"),
    ],
}


class ReasonerAgent:
    """
    Generates an ordered list of RepairProposals for a given classification.

    The proposals are deterministic: the same classification always
    produces the same proposals in the same order.
    """

    def propose(
        self,
        classification: FailureClassification,
        metadata: ElementMetadata = None,
    ) -> List[RepairProposal]:
        """
        Return an ordered list of repair proposals.

        Args:
            classification: Output from ClassifierAgent.
            metadata: Optional element metadata for context enrichment.

        Returns:
            List of RepairProposal (best first).
        """
        ftype = classification.failure_type
        entries = _STRATEGY_MAP.get(ftype, _STRATEGY_MAP[FailureType.UNKNOWN])

        proposals: List[RepairProposal] = []
        for strategy, base_confidence, risk, description in entries:
            # Adjust confidence by classification confidence
            adjusted = round(base_confidence * classification.confidence, 4)

            changes = self._build_changes(strategy, metadata)

            proposals.append(RepairProposal(
                strategy=strategy,
                description=description,
                proposed_changes=changes,
                confidence=adjusted,
                safety_risk=risk,
            ))

        logger.info(
            f"[Reasoner] {len(proposals)} proposals for {ftype.value}: "
            + ", ".join(f"{p.strategy.value}({p.confidence:.2f})" for p in proposals)
        )
        return proposals

    # ------------------------------------------------------------------

    @staticmethod
    def _build_changes(strategy: RepairStrategy, metadata: ElementMetadata = None) -> dict:
        """Build strategy-specific proposed_changes dict."""
        if strategy in (
            RepairStrategy.TEXT_BASED,
            RepairStrategy.ATTRIBUTE_BASED,
            RepairStrategy.AI_BASED,
            RepairStrategy.SELECTOR_FALLBACK,
        ):
            return {
                "element_name": metadata.name if metadata else "",
                "original_selector": metadata.selector if metadata else "",
                "type": "runtime_locator_healing",
            }

        if strategy == RepairStrategy.INCREASE_WAIT:
            return {
                "type": "increase_timeout",
                "multiplier": 1.5,
            }

        if strategy == RepairStrategy.RETRY:
            return {
                "type": "retry",
                "max_retries": 3,
                "backoff_seconds": [1, 2, 4],
            }

        return {"type": "manual_review"}
