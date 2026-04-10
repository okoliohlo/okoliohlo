"""
Self-Healing Module — Unified SQLite Database Manager
Thread-safe singleton that owns every table used by the self-healing system.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from config.config import config
from utilities.logger import get_logger

logger = get_logger(__name__)


class HealingDatabase:
    """
    Thread-safe singleton SQLite database for the self-healing module.

    Tables
    ------
    element_metadata   — latest snapshot of every known element
    selector_history   — chronological log of selector changes
    healing_memory     — past healing experiences (signature-keyed)
    audit_log          — immutable audit trail of every healing action
    """

    _instance: Optional["HealingDatabase"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.db_path: Path = config.reports_dir / "self_healing.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()
        logger.info(f"HealingDatabase initialized: {self.db_path}")

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _get_connection(self) -> sqlite3.Connection:
        """Return a thread-local connection with WAL mode enabled."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    @contextmanager
    def connection(self):
        """Context manager that yields a connection and commits on success."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    # ------------------------------------------------------------------
    # Schema initialization
    # ------------------------------------------------------------------

    def _init_schema(self):
        """Create all tables if they do not exist."""
        with self.connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS element_metadata (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    selector    TEXT    NOT NULL,
                    tag_name    TEXT    DEFAULT '',
                    text        TEXT    DEFAULT '',
                    attributes  TEXT    DEFAULT '{}',
                    position    TEXT    DEFAULT '{}',
                    css_classes TEXT    DEFAULT '[]',
                    timestamp   TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS selector_history (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    element_name  TEXT    NOT NULL,
                    old_selector  TEXT    NOT NULL,
                    new_selector  TEXT    NOT NULL,
                    strategy      TEXT    DEFAULT '',
                    confidence    REAL    DEFAULT 0.0,
                    timestamp     TEXT    NOT NULL,
                    environment   TEXT    DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS healing_memory (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    failure_signature   TEXT    NOT NULL UNIQUE,
                    failure_type        TEXT    NOT NULL,
                    element_name        TEXT    DEFAULT '',
                    original_selector   TEXT    DEFAULT '',
                    healed_selector     TEXT    DEFAULT '',
                    strategy            TEXT    NOT NULL,
                    confidence          REAL    DEFAULT 0.0,
                    success_count       INTEGER DEFAULT 0,
                    failure_count       INTEGER DEFAULT 0,
                    last_used           TEXT    NOT NULL,
                    created_at          TEXT    NOT NULL,
                    details             TEXT    DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id      TEXT    NOT NULL UNIQUE,
                    timestamp     TEXT    NOT NULL,
                    action        TEXT    NOT NULL,
                    element_name  TEXT    DEFAULT '',
                    old_selector  TEXT    DEFAULT '',
                    new_selector  TEXT    DEFAULT '',
                    strategy      TEXT    DEFAULT '',
                    confidence    REAL    DEFAULT 0.0,
                    success       INTEGER DEFAULT 0,
                    details       TEXT    DEFAULT '{}',
                    environment   TEXT    DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_memory_signature
                    ON healing_memory(failure_signature);
                CREATE INDEX IF NOT EXISTS idx_memory_element
                    ON healing_memory(element_name);
                CREATE INDEX IF NOT EXISTS idx_audit_element
                    ON audit_log(element_name);
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                    ON audit_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_history_element
                    ON selector_history(element_name);
            """)

    # ------------------------------------------------------------------
    # Element Metadata CRUD
    # ------------------------------------------------------------------

    def store_element(self, name: str, selector: str, tag_name: str = "",
                      text: str = "", attributes: Dict = None,
                      position: Dict = None, css_classes: List = None):
        """Insert or update element metadata."""
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO element_metadata
                    (name, selector, tag_name, text, attributes, position, css_classes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    selector   = excluded.selector,
                    tag_name   = excluded.tag_name,
                    text       = excluded.text,
                    attributes = excluded.attributes,
                    position   = excluded.position,
                    css_classes= excluded.css_classes,
                    timestamp  = excluded.timestamp
            """, (
                name, selector, tag_name, text,
                json.dumps(attributes or {}),
                json.dumps(position or {}),
                json.dumps(css_classes or []),
                datetime.now().isoformat(),
            ))

    def get_element(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve element metadata by logical name."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM element_metadata WHERE name = ?", (name,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row, json_fields=["attributes", "position", "css_classes"])

    # ------------------------------------------------------------------
    # Selector History
    # ------------------------------------------------------------------

    def record_selector_change(self, element_name: str, old_selector: str,
                               new_selector: str, strategy: str = "",
                               confidence: float = 0.0):
        """Append a selector change to history."""
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO selector_history
                    (element_name, old_selector, new_selector, strategy, confidence, timestamp, environment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                element_name, old_selector, new_selector, strategy,
                confidence, datetime.now().isoformat(), config.environment,
            ))

    def get_selector_history(self, element_name: str, limit: int = 20) -> List[Dict]:
        """Get recent selector history for an element."""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT * FROM selector_history
                WHERE element_name = ?
                ORDER BY timestamp DESC LIMIT ?
            """, (element_name, limit)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Healing Memory
    # ------------------------------------------------------------------

    def store_memory(self, signature: str, failure_type: str,
                     element_name: str, original_selector: str,
                     healed_selector: str, strategy: str,
                     confidence: float, success: bool,
                     details: Dict = None):
        """Insert or update a healing memory entry."""
        now = datetime.now().isoformat()
        with self.connection() as conn:
            existing = conn.execute(
                "SELECT id, success_count, failure_count FROM healing_memory WHERE failure_signature = ?",
                (signature,)
            ).fetchone()

            if existing:
                sc = existing["success_count"] + (1 if success else 0)
                fc = existing["failure_count"] + (0 if success else 1)
                conn.execute("""
                    UPDATE healing_memory SET
                        healed_selector = ?, strategy = ?, confidence = ?,
                        success_count = ?, failure_count = ?,
                        last_used = ?, details = ?
                    WHERE failure_signature = ?
                """, (
                    healed_selector, strategy, confidence,
                    sc, fc, now, json.dumps(details or {}), signature,
                ))
            else:
                conn.execute("""
                    INSERT INTO healing_memory
                        (failure_signature, failure_type, element_name, original_selector,
                         healed_selector, strategy, confidence,
                         success_count, failure_count, last_used, created_at, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    signature, failure_type, element_name, original_selector,
                    healed_selector, strategy, confidence,
                    1 if success else 0, 0 if success else 1,
                    now, now, json.dumps(details or {}),
                ))

    def lookup_memory(self, signature: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory entry by its failure signature."""
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM healing_memory WHERE failure_signature = ?",
                (signature,)
            ).fetchone()
        if row is None:
            return None
        return self._row_to_dict(row, json_fields=["details"])

    def lookup_memory_by_element(self, element_name: str) -> List[Dict]:
        """Retrieve all memory entries for a given element, ordered by success rate."""
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT *,
                    CASE WHEN (success_count + failure_count) > 0
                         THEN CAST(success_count AS REAL) / (success_count + failure_count)
                         ELSE 0.0
                    END AS success_rate
                FROM healing_memory
                WHERE element_name = ?
                ORDER BY success_rate DESC, last_used DESC
            """, (element_name,)).fetchall()
        return [self._row_to_dict(r, json_fields=["details"]) for r in rows]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Aggregate statistics from healing memory."""
        with self.connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*)                          AS total_entries,
                    SUM(success_count)                AS total_successes,
                    SUM(failure_count)                AS total_failures,
                    AVG(CASE WHEN (success_count + failure_count) > 0
                         THEN CAST(success_count AS REAL) / (success_count + failure_count)
                         ELSE 0 END)                  AS avg_success_rate
                FROM healing_memory
            """).fetchone()
        return dict(row) if row else {}

    # ------------------------------------------------------------------
    # Audit Log
    # ------------------------------------------------------------------

    def write_audit(self, entry_id: str, action: str, element_name: str,
                    old_selector: str, new_selector: str = "",
                    strategy: str = "", confidence: float = 0.0,
                    success: bool = False, details: Dict = None):
        """Append an immutable audit log entry."""
        with self.connection() as conn:
            conn.execute("""
                INSERT INTO audit_log
                    (entry_id, timestamp, action, element_name, old_selector,
                     new_selector, strategy, confidence, success, details, environment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id, datetime.now().isoformat(), action,
                element_name, old_selector, new_selector, strategy,
                confidence, int(success), json.dumps(details or {}),
                config.environment,
            ))

    def get_audit_log(self, element_name: str = None,
                      limit: int = 50) -> List[Dict]:
        """Query audit log, optionally filtered by element."""
        with self.connection() as conn:
            if element_name:
                rows = conn.execute("""
                    SELECT * FROM audit_log
                    WHERE element_name = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (element_name, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM audit_log
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,)).fetchall()
        return [self._row_to_dict(r, json_fields=["details"]) for r in rows]

    def get_audit_stats(self) -> Dict[str, Any]:
        """Aggregate statistics from the audit log."""
        with self.connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*)                AS total_actions,
                    SUM(success)            AS successful_actions,
                    AVG(success)            AS success_rate
                FROM audit_log
            """).fetchone()
        return dict(row) if row else {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_dict(row: sqlite3.Row,
                     json_fields: List[str] = None) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a plain dict, parsing JSON columns."""
        d = dict(row)
        for key in (json_fields or []):
            if key in d and isinstance(d[key], str):
                try:
                    d[key] = json.loads(d[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    def close(self):
        """Close the thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
