"""
Self-Healing Module — Locator Repository
Thin wrapper around HealingDatabase for backward compatibility.
All persistence is now handled by the unified SQLite database.
"""

from typing import Dict, List, Optional

from ai.self_healing.schemas import ElementMetadata
from ai.self_healing.database import HealingDatabase
from utilities.logger import get_logger

logger = get_logger(__name__)


class LocatorRepository:
    """
    Repository for storing and retrieving element metadata.

    This class delegates entirely to HealingDatabase — it exists
    to preserve the original public API used by other modules.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.db = HealingDatabase()
        logger.info("LocatorRepository initialized (backed by HealingDatabase)")

    def store_metadata(self, metadata: ElementMetadata):
        """Store element metadata."""
        self.db.store_element(
            name=metadata.name,
            selector=metadata.selector,
            tag_name=metadata.tag_name,
            text=metadata.text,
            attributes=metadata.attributes,
            position=metadata.position,
            css_classes=metadata.css_classes,
        )
        logger.debug(f"Stored metadata for: {metadata.name}")

    def get_metadata(self, element_name: str) -> Optional[ElementMetadata]:
        """Retrieve element metadata by logical name."""
        row = self.db.get_element(element_name)
        if row is None:
            return None
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

    def update_selector(self, element_name: str, old_selector: str,
                        new_selector: str, strategy: str = "",
                        confidence: float = 0.0):
        """Update selector and record in history."""
        # Update metadata
        existing = self.get_metadata(element_name)
        if existing:
            self.db.store_element(
                name=element_name,
                selector=new_selector,
                tag_name=existing.tag_name,
                text=existing.text,
                attributes=existing.attributes,
                position=existing.position,
                css_classes=existing.css_classes,
            )

        # Record history
        self.db.record_selector_change(
            element_name=element_name,
            old_selector=old_selector,
            new_selector=new_selector,
            strategy=strategy,
            confidence=confidence,
        )
        logger.info(f"Updated selector for {element_name}: {old_selector} -> {new_selector}")

    def get_selector_history(self, element_name: str) -> List[Dict]:
        """Get selector change history."""
        return self.db.get_selector_history(element_name)
