"""
Self-Healing Module — Classifier Agent
Deterministic failure classification using weighted pattern matching.
No randomness — confidence is derived from match-count and pattern weights.
"""

import re
from typing import Dict, List, Tuple

from ai.self_healing.schemas import (
    FailureType, FailureClassification, ElementMetadata,
)
from utilities.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pattern definitions: (regex, weight)
# ---------------------------------------------------------------------------

_PATTERNS: Dict[FailureType, List[Tuple[str, float]]] = {
    FailureType.LOCATOR_CHANGE: [
        (r"unable to locate element", 1.0),
        (r"no\s*such\s*element", 1.0),
        (r"element\s*not\s*found", 1.0),
        (r"selector.*not\s*found", 0.9),
        (r"cannot find element", 0.9),
        (r"element.*could not be found", 0.9),
        (r"locator.*resolved to.*elements", 0.8),
        (r"waiting for locator", 0.7),
    ],
    FailureType.TIMING_ISSUE: [
        (r"timeout\s*exception", 1.0),
        (r"timeout.*exceeded", 1.0),
        (r"element not visible", 0.9),
        (r"wait.*timeout", 0.9),
        (r"loading.*timeout", 0.8),
        (r"element.*not interactable", 0.8),
        (r"stale element reference", 0.8),
        (r"element not clickable", 0.7),
    ],
    FailureType.API_SCHEMA_CHANGE: [
        (r"400 bad request", 1.0),
        (r"422 unprocessable", 1.0),
        (r"schema.*validation", 0.9),
        (r"invalid.*response", 0.8),
        (r"unexpected.*format", 0.8),
        (r"missing.*field", 0.7),
        (r"validation.*error", 0.7),
    ],
    FailureType.ENVIRONMENT: [
        (r"connection refused", 1.0),
        (r"network error", 1.0),
        (r"service unavailable", 0.9),
        (r"database.*connection", 0.8),
        (r"host.*unreachable", 0.8),
        (r"server.*error", 0.7),
        (r"econnrefused", 0.9),
    ],
    FailureType.DATA_ISSUE: [
        (r"assertion\s*error", 1.0),
        (r"expected.*but got", 0.9),
        (r"data.*mismatch", 0.8),
        (r"assert.*failed", 0.8),
        (r"value.*not equal", 0.7),
        (r"unexpected.*value", 0.7),
    ],
}


class ClassifierAgent:
    """
    Deterministic failure classifier.

    Scoring algorithm:
    1. Concatenate error message + stack trace.
    2. For each FailureType, sum (match_count * pattern_weight).
    3. Normalize scores → confidence = best_score / total_score.
    4. Clamp confidence to [0.30, 0.95].
    """

    def classify(
        self,
        error_message: str,
        stack_trace: str = "",
        metadata: ElementMetadata = None,
    ) -> FailureClassification:
        """Classify a failure into a FailureType."""
        text = f"{error_message} {stack_trace}".lower()

        scores: Dict[FailureType, float] = {}
        indicators: Dict[FailureType, List[str]] = {}

        for ftype, patterns in _PATTERNS.items():
            type_score = 0.0
            type_indicators: List[str] = []
            for pattern, weight in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    type_score += len(matches) * weight
                    type_indicators.extend(matches[:2])
            if type_score > 0:
                scores[ftype] = type_score
                indicators[ftype] = type_indicators[:5]

        if not scores:
            # If we have metadata and the selector is present, likely locator
            if metadata and metadata.selector:
                return FailureClassification(
                    failure_type=FailureType.LOCATOR_CHANGE,
                    confidence=0.40,
                    reasoning="No pattern matched but context suggests locator failure",
                    key_indicators=[],
                )
            return FailureClassification(
                failure_type=FailureType.UNKNOWN,
                confidence=0.20,
                reasoning="No recognizable failure patterns detected",
                key_indicators=[],
            )

        best_type = max(scores, key=scores.get)
        total = sum(scores.values())
        raw_confidence = scores[best_type] / total

        # Boost when only one type matched
        if len(scores) == 1:
            raw_confidence = min(0.95, raw_confidence + 0.20)

        confidence = max(0.30, min(0.95, raw_confidence))

        reasoning = self._build_reasoning(best_type, indicators.get(best_type, []), confidence)

        logger.info(
            f"[Classifier] {best_type.value} confidence={confidence:.2f} "
            f"({len(scores)} types matched)"
        )

        return FailureClassification(
            failure_type=best_type,
            confidence=confidence,
            reasoning=reasoning,
            key_indicators=indicators.get(best_type, []),
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _build_reasoning(ftype: FailureType, indicators: List[str], confidence: float) -> str:
        level = "high" if confidence > 0.80 else ("moderate" if confidence > 0.60 else "low")
        if not indicators:
            return f"Classified as {ftype.value} with {level} confidence"
        primary = indicators[0]
        extra = f" (and {len(indicators) - 1} more)" if len(indicators) > 1 else ""
        return f"Detected '{primary}'{extra} → {ftype.value} ({level} confidence)"
