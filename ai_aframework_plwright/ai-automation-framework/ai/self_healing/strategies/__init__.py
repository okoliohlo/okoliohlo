"""
Self-Healing Module — Strategy Registry
Exports all strategies and provides a factory for building the ordered strategy chain.
"""

from typing import List
from playwright.sync_api import Page

from ai.self_healing.strategies.base import BaseHealingStrategy
from ai.self_healing.strategies.text_based import TextBasedHealing
from ai.self_healing.strategies.attribute_based import AttributeBasedHealing
from ai.self_healing.strategies.ai_based import AIBasedHealing

__all__ = [
    "BaseHealingStrategy",
    "TextBasedHealing",
    "AttributeBasedHealing",
    "AIBasedHealing",
    "build_strategy_chain",
]


def build_strategy_chain(page: Page, include_ai: bool = True) -> List[BaseHealingStrategy]:
    """
    Build the ordered list of healing strategies.

    Strategies are sorted by priority (lower = tried first):
      10 — TextBasedHealing
      20 — AttributeBasedHealing
      30 — AIBasedHealing (optional)
    """
    strategies: List[BaseHealingStrategy] = [
        TextBasedHealing(page),
        AttributeBasedHealing(page),
    ]
    if include_ai:
        strategies.append(AIBasedHealing(page))

    strategies.sort(key=lambda s: s.priority)
    return strategies
