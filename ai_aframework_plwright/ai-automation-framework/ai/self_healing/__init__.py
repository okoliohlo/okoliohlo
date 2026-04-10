"""
Self-Healing Module
===================
Unified self-healing system for Playwright-based test automation.

Architecture:
  HealingEngine          — public facade (used by DriverFactory)
  HealingCoordinator     — multi-agent orchestrator
  ClassifierAgent        — deterministic failure classification
  ReasonerAgent          — repair proposal generation
  ExecutorAgent          — strategy execution + validation
  HealingDatabase        — thread-safe SQLite persistence
  LocatorRepository      — backward-compatible metadata API
  ElementValidator       — multi-check element validation
  strategies/            — text, attribute, AI-based healing

Quick start:
    from ai.self_healing.healing_engine import HealingEngine
    engine = HealingEngine(page)
"""

from ai.self_healing.healing_engine import HealingEngine
from ai.self_healing.schemas import (
    ElementMetadata,
    HealingResult,
    HealingStrategyResult,
    FailureType,
    RepairStrategy,
    SafetyMode,
)
from ai.self_healing.locator_repository import LocatorRepository
from ai.self_healing.database import HealingDatabase
from ai.self_healing.element_validator import ElementValidator

__all__ = [
    "HealingEngine",
    "HealingResult",
    "HealingStrategyResult",
    "ElementMetadata",
    "LocatorRepository",
    "HealingDatabase",
    "ElementValidator",
    "FailureType",
    "RepairStrategy",
    "SafetyMode",
]