"""
Integration tests for the unified self-healing module.

Tests cover:
  - HealingDatabase CRUD operations
  - ClassifierAgent deterministic classification
  - ReasonerAgent proposal generation
  - ElementValidator scoring
  - LocatorRepository backward compatibility
  - HealingCoordinator pipeline (with mocked Page)
  - End-to-end HealingEngine flow (with mocked Page)
"""

import os
import json
import sqlite3
import tempfile
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _patch_config(tmp_path):
    """Redirect all DB/report paths to a temp directory."""
    with patch("ai.self_healing.database.config") as mock_cfg:
        mock_cfg.reports_dir = tmp_path / "reports"
        mock_cfg.reports_dir.mkdir(parents=True, exist_ok=True)
        mock_cfg.environment = "test"
        mock_cfg.ai_analysis_enabled = True

        # Reset singleton so each test gets a fresh DB
        from ai.self_healing.database import HealingDatabase
        HealingDatabase._instance = None
        HealingDatabase._lock = __import__("threading").Lock()

        yield mock_cfg

        HealingDatabase._instance = None


@pytest.fixture
def db():
    from ai.self_healing.database import HealingDatabase
    return HealingDatabase()


@pytest.fixture
def sample_metadata():
    from ai.self_healing.schemas import ElementMetadata
    return ElementMetadata(
        name="pay_button",
        selector="#pay-btn",
        tag_name="button",
        text="Pay Now",
        attributes={"data-testid": "pay-btn", "type": "submit"},
        css_classes=["btn", "btn-primary"],
    )


# ===========================================================================
# 1. HealingDatabase
# ===========================================================================

class TestHealingDatabase:

    def test_store_and_get_element(self, db):
        db.store_element(
            name="login_btn", selector="#login",
            tag_name="button", text="Log In",
            attributes={"role": "button"}, css_classes=["btn"],
        )
        row = db.get_element("login_btn")
        assert row is not None
        assert row["name"] == "login_btn"
        assert row["selector"] == "#login"
        assert row["tag_name"] == "button"
        assert row["attributes"] == {"role": "button"}
        assert row["css_classes"] == ["btn"]

    def test_get_element_missing(self, db):
        assert db.get_element("nonexistent") is None

    def test_upsert_element(self, db):
        db.store_element(name="el", selector=".old")
        db.store_element(name="el", selector=".new")
        row = db.get_element("el")
        assert row["selector"] == ".new"

    def test_selector_history(self, db):
        db.record_selector_change("el", ".old", ".new", strategy="text", confidence=0.9)
        db.record_selector_change("el", ".new", ".newest", strategy="attr", confidence=0.8)
        history = db.get_selector_history("el")
        assert len(history) == 2
        assert history[0]["new_selector"] == ".newest"  # newest first

    def test_store_and_lookup_memory(self, db):
        db.store_memory(
            signature="abc123", failure_type="LOCATOR_CHANGE",
            element_name="btn", original_selector="#old",
            healed_selector="#new", strategy="text",
            confidence=0.85, success=True,
        )
        mem = db.lookup_memory("abc123")
        assert mem is not None
        assert mem["success_count"] == 1
        assert mem["failure_count"] == 0

    def test_memory_updates_counts(self, db):
        db.store_memory("sig1", "LOCATOR_CHANGE", "btn", "#o", "#n", "text", 0.9, True)
        db.store_memory("sig1", "LOCATOR_CHANGE", "btn", "#o", "#n", "text", 0.9, True)
        db.store_memory("sig1", "LOCATOR_CHANGE", "btn", "#o", "#n", "text", 0.5, False)
        mem = db.lookup_memory("sig1")
        assert mem["success_count"] == 2
        assert mem["failure_count"] == 1

    def test_memory_by_element(self, db):
        db.store_memory("s1", "LOCATOR_CHANGE", "btn", "#a", "#b", "text", 0.9, True)
        db.store_memory("s2", "TIMING_ISSUE", "btn", "#a", "#c", "wait", 0.7, False)
        results = db.lookup_memory_by_element("btn")
        assert len(results) == 2

    def test_memory_stats(self, db):
        db.store_memory("s1", "LOCATOR_CHANGE", "a", "#x", "#y", "t", 0.9, True)
        stats = db.get_memory_stats()
        assert stats["total_entries"] == 1
        assert stats["total_successes"] == 1

    def test_audit_log(self, db):
        db.write_audit(
            entry_id="e1", action="healed", element_name="btn",
            old_selector="#old", new_selector="#new",
            strategy="text", confidence=0.9, success=True,
        )
        logs = db.get_audit_log("btn")
        assert len(logs) == 1
        assert logs[0]["action"] == "healed"
        assert logs[0]["success"] == 1

    def test_audit_stats(self, db):
        db.write_audit("e1", "healed", "a", "#o", success=True)
        db.write_audit("e2", "failed", "a", "#o", success=False)
        stats = db.get_audit_stats()
        assert stats["total_actions"] == 2
        assert stats["successful_actions"] == 1


# ===========================================================================
# 2. ClassifierAgent
# ===========================================================================

class TestClassifierAgent:

    @pytest.fixture
    def classifier(self):
        from ai.self_healing.agents.classifier import ClassifierAgent
        return ClassifierAgent()

    @pytest.mark.parametrize("error,expected_type", [
        ("NoSuchElementException: Unable to locate element: #pay-btn", "LOCATOR_CHANGE"),
        ("Element not found: .checkout", "LOCATOR_CHANGE"),
        ("TimeoutException: waiting for locator timeout exceeded", "TIMING_ISSUE"),
        ("element not visible after 30s", "TIMING_ISSUE"),
        ("422 Unprocessable Entity: validation error", "API_SCHEMA_CHANGE"),
        ("400 Bad Request: missing field 'email'", "API_SCHEMA_CHANGE"),
        ("Connection refused: localhost:5432", "ENVIRONMENT"),
        ("Network error: ECONNREFUSED", "ENVIRONMENT"),
        ("AssertionError: expected 'foo' but got 'bar'", "DATA_ISSUE"),
    ])
    def test_deterministic_classification(self, classifier, error, expected_type):
        result = classifier.classify(error_message=error)
        assert result.failure_type.value == expected_type
        assert 0.30 <= result.confidence <= 0.95

    def test_unknown_classification(self, classifier):
        result = classifier.classify(error_message="something completely random")
        assert result.failure_type.value == "UNKNOWN"
        assert result.confidence == 0.20

    def test_same_input_same_output(self, classifier):
        """Verify determinism — same input always yields same result."""
        r1 = classifier.classify("Unable to locate element #btn")
        r2 = classifier.classify("Unable to locate element #btn")
        assert r1.failure_type == r2.failure_type
        assert r1.confidence == r2.confidence
        assert r1.key_indicators == r2.key_indicators

    def test_metadata_hint_for_unknown(self, classifier):
        """When no pattern matches but metadata exists, default to LOCATOR_CHANGE."""
        from ai.self_healing.schemas import ElementMetadata
        meta = ElementMetadata(name="btn", selector="#btn")
        result = classifier.classify("weird error xyz", metadata=meta)
        assert result.failure_type.value == "LOCATOR_CHANGE"
        assert result.confidence == 0.40


# ===========================================================================
# 3. ReasonerAgent
# ===========================================================================

class TestReasonerAgent:

    @pytest.fixture
    def reasoner(self):
        from ai.self_healing.agents.reasoner import ReasonerAgent
        return ReasonerAgent()

    def test_locator_proposals(self, reasoner, sample_metadata):
        from ai.self_healing.schemas import FailureClassification, FailureType
        classification = FailureClassification(
            failure_type=FailureType.LOCATOR_CHANGE,
            confidence=0.90, reasoning="test",
        )
        proposals = reasoner.propose(classification, sample_metadata)
        assert len(proposals) >= 3
        assert proposals[0].strategy.value == "TEXT_BASED"
        # Confidence = base * classification.confidence
        assert proposals[0].confidence == pytest.approx(0.90 * 0.90, abs=0.01)

    def test_timing_proposals(self, reasoner):
        from ai.self_healing.schemas import FailureClassification, FailureType
        classification = FailureClassification(
            failure_type=FailureType.TIMING_ISSUE,
            confidence=0.80, reasoning="test",
        )
        proposals = reasoner.propose(classification)
        strategies = [p.strategy.value for p in proposals]
        assert "INCREASE_WAIT" in strategies
        assert "RETRY" in strategies

    def test_deterministic_proposals(self, reasoner, sample_metadata):
        from ai.self_healing.schemas import FailureClassification, FailureType
        c = FailureClassification(failure_type=FailureType.LOCATOR_CHANGE, confidence=0.85, reasoning="x")
        p1 = reasoner.propose(c, sample_metadata)
        p2 = reasoner.propose(c, sample_metadata)
        assert len(p1) == len(p2)
        for a, b in zip(p1, p2):
            assert a.strategy == b.strategy
            assert a.confidence == b.confidence


# ===========================================================================
# 4. ElementValidator
# ===========================================================================

class TestElementValidator:

    @pytest.fixture
    def validator(self):
        from ai.self_healing.element_validator import ElementValidator
        return ElementValidator()

    def _make_locator(self, tag="button", text="Pay Now", visible=True,
                      attrs=None):
        """Create a mock Playwright Locator."""
        locator = MagicMock()
        locator.first.evaluate.return_value = tag
        locator.text_content.return_value = text
        locator.is_visible.return_value = visible
        locator.is_enabled.return_value = True
        locator.get_attribute.side_effect = lambda a: (attrs or {}).get(a)
        return locator

    def test_perfect_match(self, validator, sample_metadata):
        locator = self._make_locator(
            tag="button", text="Pay Now",
            attrs={"data-testid": "pay-btn"},
        )
        assert validator.validate(locator, sample_metadata) is True
        score = validator.score(locator, sample_metadata)
        assert score >= 0.85

    def test_tag_mismatch(self, validator, sample_metadata):
        locator = self._make_locator(tag="div", text="Pay Now")
        score = validator.score(locator, sample_metadata)
        # Tag is 0.20 weight, div != button → 0 for tag
        assert score < 1.0

    def test_text_mismatch(self, validator, sample_metadata):
        locator = self._make_locator(tag="button", text="Submit")
        score = validator.score(locator, sample_metadata)
        assert score < 0.80

    def test_invisible_element_penalty(self, validator, sample_metadata):
        locator = self._make_locator(visible=False)
        locator.is_enabled.return_value = False
        score_invisible = validator.score(locator, sample_metadata)
        locator2 = self._make_locator(visible=True)
        score_visible = validator.score(locator2, sample_metadata)
        assert score_visible > score_invisible

    def test_no_constraints_passes(self, validator):
        from ai.self_healing.schemas import ElementMetadata
        meta = ElementMetadata(name="x", selector="#x")
        locator = self._make_locator()
        # No tag, text, or attributes to check → should pass
        assert validator.validate(locator, meta) is True


# ===========================================================================
# 5. LocatorRepository (backward compat)
# ===========================================================================

class TestLocatorRepository:

    @pytest.fixture
    def repo(self):
        from ai.self_healing.locator_repository import LocatorRepository
        # Reset singleton
        LocatorRepository._instance = None
        return LocatorRepository()

    def test_store_and_get(self, repo, sample_metadata):
        repo.store_metadata(sample_metadata)
        result = repo.get_metadata("pay_button")
        assert result is not None
        assert result.name == "pay_button"
        assert result.selector == "#pay-btn"
        assert result.tag_name == "button"

    def test_update_selector(self, repo, sample_metadata):
        repo.store_metadata(sample_metadata)
        repo.update_selector("pay_button", "#pay-btn", "[data-testid='pay']", "text", 0.9)
        result = repo.get_metadata("pay_button")
        assert result.selector == "[data-testid='pay']"

    def test_selector_history(self, repo, sample_metadata):
        repo.store_metadata(sample_metadata)
        repo.update_selector("pay_button", "#pay-btn", ".new1")
        repo.update_selector("pay_button", ".new1", ".new2")
        history = repo.get_selector_history("pay_button")
        assert len(history) == 2

    def test_get_missing_returns_none(self, repo):
        assert repo.get_metadata("no_such_element") is None


# ===========================================================================
# 6. Strategy tests (with mocked Page)
# ===========================================================================

class TestStrategies:

    def _mock_page(self):
        page = MagicMock()
        return page

    def _make_single_locator(self, page):
        """Configure page.locator() to return a locator matching exactly 1 element."""
        locator = MagicMock()
        locator.count.return_value = 1
        locator.text_content.return_value = "Pay Now"
        page.locator.return_value = locator
        page.get_by_text.return_value = locator
        page.get_by_role.return_value = locator
        return locator

    def test_text_based_success(self, sample_metadata):
        from ai.self_healing.strategies.text_based import TextBasedHealing
        page = self._mock_page()
        self._make_single_locator(page)
        strategy = TextBasedHealing(page)
        result = strategy.heal(sample_metadata)
        assert result.success is True
        assert result.confidence > 0

    def test_text_based_no_text(self):
        from ai.self_healing.strategies.text_based import TextBasedHealing
        from ai.self_healing.schemas import ElementMetadata
        page = self._mock_page()
        meta = ElementMetadata(name="x", selector="#x", text="")
        result = TextBasedHealing(page).heal(meta)
        assert result.success is False

    def test_attribute_based_success(self, sample_metadata):
        from ai.self_healing.strategies.attribute_based import AttributeBasedHealing
        page = self._mock_page()
        self._make_single_locator(page)
        strategy = AttributeBasedHealing(page)
        result = strategy.heal(sample_metadata)
        assert result.success is True
        assert result.confidence >= 0.90

    def test_attribute_based_no_attrs(self):
        from ai.self_healing.strategies.attribute_based import AttributeBasedHealing
        from ai.self_healing.schemas import ElementMetadata
        page = self._mock_page()
        meta = ElementMetadata(name="x", selector="#x", attributes={})
        result = AttributeBasedHealing(page).heal(meta)
        assert result.success is False

    def test_build_strategy_chain_ordering(self):
        from ai.self_healing.strategies import build_strategy_chain
        page = self._mock_page()
        chain = build_strategy_chain(page, include_ai=True)
        assert len(chain) == 3
        priorities = [s.priority for s in chain]
        assert priorities == sorted(priorities)

    def test_build_strategy_chain_without_ai(self):
        from ai.self_healing.strategies import build_strategy_chain
        page = self._mock_page()
        chain = build_strategy_chain(page, include_ai=False)
        assert len(chain) == 2


# ===========================================================================
# 7. Coordinator Integration (mocked Page)
# ===========================================================================

class TestHealingCoordinator:

    @pytest.fixture
    def coordinator(self):
        from ai.self_healing.agents.coordinator import HealingCoordinator
        page = MagicMock()

        # Set up page.locator() to return single-match locator
        locator = MagicMock()
        locator.count.return_value = 1
        locator.text_content.return_value = "Pay Now"
        locator.first.evaluate.return_value = "button"
        locator.is_visible.return_value = True
        locator.is_enabled.return_value = True
        locator.get_attribute.side_effect = lambda a: {"data-testid": "pay-btn"}.get(a)
        locator.element_handle.return_value = MagicMock()
        locator.wait_for.return_value = None

        page.locator.return_value = locator
        page.get_by_text.return_value = locator
        page.get_by_role.return_value = locator
        page.evaluate.return_value = []

        return HealingCoordinator(page, max_attempts=3, include_ai=False)

    def test_heal_with_stored_metadata(self, coordinator, db, sample_metadata):
        # Pre-store metadata
        db.store_element(
            name="pay_button", selector="#pay-btn",
            tag_name="button", text="Pay Now",
            attributes={"data-testid": "pay-btn"},
            css_classes=["btn"],
        )

        result = coordinator.heal(
            selector="#pay-btn",
            element_name="pay_button",
            error_message="Element not found: #pay-btn",
        )
        assert result.success is True
        assert result.strategy is not None
        assert result.confidence > 0

    def test_heal_without_metadata(self, coordinator):
        result = coordinator.heal(
            selector="#nonexistent",
            element_name="unknown_element",
            error_message="Element not found",
        )
        # Should still attempt healing with stub metadata
        # Success depends on mock page responses
        assert isinstance(result.success, bool)
        assert result.attempts >= 0

    def test_heal_records_to_audit(self, coordinator, db, sample_metadata):
        db.store_element(
            name="pay_button", selector="#pay-btn",
            tag_name="button", text="Pay Now",
            attributes={"data-testid": "pay-btn"},
        )
        coordinator.heal("#pay-btn", "pay_button", "Element not found")
        logs = db.get_audit_log("pay_button")
        assert len(logs) >= 1

    def test_heal_records_to_memory(self, coordinator, db):
        db.store_element(name="btn", selector="#btn", tag_name="button", text="Click")
        coordinator.heal("#btn", "btn", "Element not found")
        memories = db.lookup_memory_by_element("btn")
        assert len(memories) >= 1

    def test_memory_recall(self, coordinator, db):
        """When memory has a successful heal, it should be tried first."""
        db.store_element(name="btn2", selector="#old", tag_name="button", text="OK")
        # Seed memory with a successful heal
        sig = coordinator._signature(
            type("M", (), {"name": "btn2", "selector": "#old"})()
        )
        db.store_memory(
            signature=sig, failure_type="LOCATOR_CHANGE",
            element_name="btn2", original_selector="#old",
            healed_selector="#new", strategy="text",
            confidence=0.90, success=True,
        )
        # Bump success count to pass the 0.60 threshold
        db.store_memory(sig, "LOCATOR_CHANGE", "btn2", "#old", "#new", "text", 0.90, True)

        result = coordinator.heal("#old", "btn2", "Element not found")
        assert result.success is True
        assert result.strategy == "memory_recall"


# ===========================================================================
# 8. HealingEngine (facade)
# ===========================================================================

class TestHealingEngine:

    @pytest.fixture
    def engine(self):
        with patch("ai.self_healing.healing_engine.config") as eng_cfg:
            eng_cfg.ai_analysis_enabled = False
            eng_cfg.environment = "test"

            page = MagicMock()
            locator = MagicMock()
            locator.count.return_value = 1
            locator.text_content.return_value = "Pay"
            locator.first.evaluate.return_value = "button"
            locator.is_visible.return_value = True
            locator.is_enabled.return_value = True
            locator.get_attribute.return_value = None
            locator.wait_for.return_value = None
            locator.bounding_box.return_value = {"x": 0, "y": 0, "width": 100, "height": 40}

            elem_handle = MagicMock()
            elem_handle.evaluate.side_effect = lambda js: {
                "el => el.tagName.toLowerCase()": "button",
                "el => Array.from(el.classList)": ["btn"],
            }.get(js, {})
            locator.element_handle.return_value = elem_handle

            page.locator.return_value = locator
            page.get_by_text.return_value = locator
            page.get_by_role.return_value = locator
            page.evaluate.return_value = []

            from ai.self_healing.healing_engine import HealingEngine
            return HealingEngine(page)

    def test_record_success(self, engine, db):
        locator = engine.page.locator("#test")
        engine.record_success("test_el", "#test", locator)
        row = db.get_element("test_el")
        assert row is not None

    def test_heal_returns_result(self, engine):
        result = engine.heal("#broken", "some_btn", "Element not found")
        assert hasattr(result, "success")
        assert hasattr(result, "locator")
        assert hasattr(result, "strategy")

    def test_get_statistics(self, engine):
        stats = engine.get_statistics()
        assert "memory" in stats
        assert "audit" in stats

    def test_get_element_history(self, engine, db):
        db.store_element(name="el", selector="#el")
        db.record_selector_change("el", "#el", "#new")
        history = engine.get_element_history("el")
        assert "selector_history" in history
        assert len(history["selector_history"]) == 1
