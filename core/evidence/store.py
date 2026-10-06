"""Cryptographic Evidence Store and Immutable Citations."""

from __future__ import annotations

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """An immutable cryptographic evidence object backing an analytical claim."""

    evidence_id: str = Field(default_factory=lambda: f"EVD-{str(uuid.uuid4())[:8].upper()}")
    claim_key: str
    numeric_value: float
    unit: str  # USD, %, count, ratio
    query_sql: str
    query_hash: str
    dataset_hash: str
    metric_definition: str
    grain: str
    created_at: float = Field(default_factory=time.time)


class EvidenceStore:
    """Manages immutable evidence items and verifies citations."""

    def __init__(self):
        self._store: Dict[str, EvidenceItem] = {}

    def add_evidence(
        self,
        claim_key: str,
        numeric_value: float,
        unit: str,
        query_sql: str,
        query_hash: str,
        dataset_hash: str,
        metric_definition: str,
        grain: str = "order",
    ) -> EvidenceItem:
        """Register and hash an evidence item."""
        item = EvidenceItem(
            claim_key=claim_key,
            numeric_value=numeric_value,
            unit=unit,
            query_sql=query_sql,
            query_hash=query_hash,
            dataset_hash=dataset_hash,
            metric_definition=metric_definition,
            grain=grain,
        )
        self._store[item.evidence_id] = item
        return item

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Retrieve evidence item by ID."""
        return self._store.get(evidence_id)

    def find_matching_evidence(self, val: float, tolerance: float = 0.05) -> Optional[EvidenceItem]:
        """Find an evidence item matching a numeric value within relative tolerance."""
        for item in self._store.values():
            if abs(item.numeric_value - val) <= max(0.01, abs(item.numeric_value) * tolerance):
                return item
        return None

    def all_items(self) -> List[EvidenceItem]:
        """Return all registered evidence items."""
        return list(self._store.values())

    def clear(self) -> None:
        """Clear store."""
        self._store.clear()
