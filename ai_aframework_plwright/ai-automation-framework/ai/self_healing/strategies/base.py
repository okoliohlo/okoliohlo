"""
Self-Healing Module — Base Healing Strategy
Abstract base class that every concrete strategy must implement.
"""

from abc import ABC, abstractmethod
from playwright.sync_api import Page
from ai.self_healing.schemas import ElementMetadata, HealingStrategyResult
from utilities.logger import get_logger

logger = get_logger(__name__)


class BaseHealingStrategy(ABC):
    """
    Abstract base for all runtime healing strategies.

    Every strategy receives the Playwright Page and stored ElementMetadata,
    then attempts to locate the element using its own heuristic.
    """

    def __init__(self, page: Page, name: str, priority: int = 100):
        """
        Args:
            page: Live Playwright Page instance.
            name: Human-readable strategy name.
            priority: Lower number = tried first.
        """
        self.page = page
        self.name = name
        self.priority = priority

    @abstractmethod
    def heal(self, metadata: ElementMetadata) -> HealingStrategyResult:
        """
        Attempt to re-locate an element on the live page.

        Args:
            metadata: Previously recorded element snapshot.

        Returns:
            HealingStrategyResult with success flag and optional locator.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} priority={self.priority}>"
