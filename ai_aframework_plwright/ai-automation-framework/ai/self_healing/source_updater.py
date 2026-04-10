"""
Self-Healing Module — Controlled Source Code Updater

Updates Page Object selectors after a successful heal, with three approval modes:

  source_update_mode (in environments.yaml features):
    "auto"    — update immediately if confidence rules pass.
    "prompt"  — pause and ask the human via terminal (Y/N).
    "pending" — queue to reports/pending_updates.json for offline review.

Guards (always enforced regardless of mode):
  1. Feature flag `source_auto_update` must be enabled.
  2. Healing confidence >= `min_confidence_for_update`.
  3. Old selector appears exactly once in the source file.
"""

import inspect
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)

_VALID_MODES = ("auto", "prompt", "pending")


class SourceUpdater:
    """Controlled updater for Page Object selector strings."""

    def __init__(self):
        self._enabled = config.is_feature_enabled("source_auto_update")
        self._mode = config.env_config.features.get(
            "source_update_mode", "prompt"
        )
        self._min_confidence = config.env_config.features.get(
            "min_confidence_for_update", 0.85
        )
        self._pending_path: Path = config.reports_dir / "pending_updates.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_if_approved(
        self,
        page_object: object,
        old_selector: str,
        new_selector: str,
        element_name: str,
        confidence: float,
        strategy: str,
    ) -> bool:
        """
        Propose a selector update and route through the configured approval mode.

        Returns True if the source file was updated in this call.
        """
        # --- Gate checks (always enforced) ---
        if not self._enabled:
            logger.info(
                f"[SourceUpdater] source_auto_update is DISABLED -- "
                f"skipping update for '{element_name}'"
            )
            return False

        if confidence < self._min_confidence:
            logger.warning(
                f"[SourceUpdater] Confidence {confidence:.2f} below threshold "
                f"{self._min_confidence:.2f} -- skipping update for '{element_name}'"
            )
            return False

        if not new_selector or new_selector == old_selector:
            return False

        source_path = self._resolve_source(page_object)
        if source_path is None:
            return False

        if not self._validate_source(source_path, old_selector):
            return False

        mode = self._mode if self._mode in _VALID_MODES else "prompt"

        # --- Route to approval mode ---
        if mode == "auto":
            return self._apply_update(
                source_path, old_selector, new_selector,
                element_name, confidence, strategy,
            )

        if mode == "prompt":
            return self._prompt_and_apply(
                source_path, old_selector, new_selector,
                element_name, confidence, strategy,
            )

        # mode == "pending"
        self._queue_pending(
            source_path, old_selector, new_selector,
            element_name, confidence, strategy,
        )
        return False

    # ------------------------------------------------------------------
    # Prompt mode — Human-in-the-Loop
    # ------------------------------------------------------------------

    def _prompt_and_apply(
        self,
        source_path: Path,
        old_selector: str,
        new_selector: str,
        element_name: str,
        confidence: float,
        strategy: str,
    ) -> bool:
        """Display the proposed change and ask the human to approve."""
        proposal = (
            f"\n{'=' * 60}\n"
            f"  SOURCE CODE UPDATE PROPOSAL\n"
            f"{'=' * 60}\n"
            f"  File:          {source_path.name}\n"
            f"  Element:       {element_name}\n"
            f"  Old selector:  {old_selector}\n"
            f"  New selector:  {new_selector}\n"
            f"  Strategy:      {strategy}\n"
            f"  Confidence:    {confidence:.2f}\n"
            f"{'=' * 60}\n"
        )

        # Print directly to stdout so it is always visible in the terminal
        sys.stdout.write(proposal)
        sys.stdout.flush()

        try:
            answer = input("  Apply this update? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer in ("y", "yes", ""):
            logger.info("[SourceUpdater] Human APPROVED the update")
            return self._apply_update(
                source_path, old_selector, new_selector,
                element_name, confidence, strategy,
            )

        logger.info("[SourceUpdater] Human REJECTED the update")
        self._queue_pending(
            source_path, old_selector, new_selector,
            element_name, confidence, strategy,
        )
        logger.info(
            f"[SourceUpdater] Rejected update saved to {self._pending_path.name} "
            f"for later review"
        )
        return False

    # ------------------------------------------------------------------
    # Pending mode — queue for offline review
    # ------------------------------------------------------------------

    def _queue_pending(
        self,
        source_path: Path,
        old_selector: str,
        new_selector: str,
        element_name: str,
        confidence: float,
        strategy: str,
    ) -> None:
        """Append the proposed change to the pending updates file."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "file": str(source_path),
            "element_name": element_name,
            "old_selector": old_selector,
            "new_selector": new_selector,
            "strategy": strategy,
            "confidence": confidence,
            "status": "pending",
        }

        pending = []
        if self._pending_path.exists():
            try:
                pending = json.loads(self._pending_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pending = []

        pending.append(entry)
        self._pending_path.write_text(
            json.dumps(pending, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        logger.info(
            f"\n{'=' * 60}\n"
            f"  SOURCE UPDATE QUEUED FOR REVIEW\n"
            f"{'=' * 60}\n"
            f"  File:          {source_path.name}\n"
            f"  Element:       {element_name}\n"
            f"  Old selector:  {old_selector}\n"
            f"  New selector:  {new_selector}\n"
            f"  Strategy:      {strategy}\n"
            f"  Confidence:    {confidence:.2f}\n"
            f"  Review file:   {self._pending_path.name}\n"
            f"{'=' * 60}"
        )

    # ------------------------------------------------------------------
    # Auto mode — direct update
    # ------------------------------------------------------------------

    def _apply_update(
        self,
        source_path: Path,
        old_selector: str,
        new_selector: str,
        element_name: str,
        confidence: float,
        strategy: str,
    ) -> bool:
        """Read source, replace selector, write back."""
        try:
            content = source_path.read_text(encoding="utf-8")
            updated = content.replace(old_selector, new_selector, 1)
            source_path.write_text(updated, encoding="utf-8")

            logger.info(
                f"\n{'=' * 60}\n"
                f"  SOURCE CODE UPDATED\n"
                f"{'=' * 60}\n"
                f"  File:          {source_path.name}\n"
                f"  Element:       {element_name}\n"
                f"  Old selector:  {old_selector}\n"
                f"  New selector:  {new_selector}\n"
                f"  Strategy:      {strategy}\n"
                f"  Confidence:    {confidence:.2f}\n"
                f"{'=' * 60}"
            )
            return True

        except Exception as e:
            logger.error(f"[SourceUpdater] Failed to update {source_path}: {e}")
            return False

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_source(page_object: object) -> Optional[Path]:
        """Find the .py file that defines the page object class."""
        try:
            source_file = inspect.getfile(page_object.__class__)
            path = Path(source_file)
            if path.exists() and path.suffix == ".py":
                return path
        except (TypeError, OSError) as e:
            logger.warning(f"[SourceUpdater] Cannot resolve source file: {e}")
        return None

    @staticmethod
    def _validate_source(source_path: Path, old_selector: str) -> bool:
        """Ensure old selector appears exactly once in the source file."""
        try:
            content = source_path.read_text(encoding="utf-8")
            occurrences = content.count(old_selector)
            if occurrences == 0:
                logger.warning(
                    f"[SourceUpdater] Old selector not found in {source_path.name}"
                )
                return False
            if occurrences > 1:
                logger.warning(
                    f"[SourceUpdater] Old selector found {occurrences} times in "
                    f"{source_path.name} -- refusing ambiguous update"
                )
                return False
            return True
        except Exception as e:
            logger.error(f"[SourceUpdater] Cannot read {source_path}: {e}")
            return False

    # ------------------------------------------------------------------
    # Utility: apply pending updates (run manually after review)
    # ------------------------------------------------------------------

    def apply_pending(self) -> int:
        """
        Apply all entries marked as 'approved' in pending_updates.json.

        Usage (from CLI):
            python -c "
            import sys; sys.path.insert(0, '.')
            from ai.self_healing.source_updater import SourceUpdater
            count = SourceUpdater().apply_pending()
            print(f'Applied {count} updates')
            "

        Returns the number of updates applied.
        """
        if not self._pending_path.exists():
            logger.info("[SourceUpdater] No pending updates file found")
            return 0

        pending = json.loads(self._pending_path.read_text(encoding="utf-8"))
        applied = 0

        for entry in pending:
            if entry.get("status") != "approved":
                continue

            source_path = Path(entry["file"])
            if not self._validate_source(source_path, entry["old_selector"]):
                entry["status"] = "failed"
                continue

            ok = self._apply_update(
                source_path,
                entry["old_selector"],
                entry["new_selector"],
                entry["element_name"],
                entry["confidence"],
                entry["strategy"],
            )
            entry["status"] = "applied" if ok else "failed"
            if ok:
                applied += 1

        self._pending_path.write_text(
            json.dumps(pending, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return applied
