"""Database Engine Abstractions and Execution Models.

Defines DatabaseEngine interface, ExecutionResult, and read-only query policies.
"""

from __future__ import annotations

import abc
import hashlib
import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
import pandas as pd


class ExecutionResult(BaseModel):
    """Immutable result of a database query execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    query_hash: str
    data_hash: str
    truncated: bool = False

    def to_df(self) -> pd.DataFrame:
        """Convert rows to a pandas DataFrame."""
        return pd.DataFrame(self.rows)


class DatabaseEngine(abc.ABC):
    """Abstract interface for read-only analytical database engines."""

    @abc.abstractmethod
    def execute_query(
        self,
        query: str,
        max_rows: int = 10000,
        timeout_seconds: float = 30.0,
    ) -> ExecutionResult:
        """Execute a read-only query and return ExecutionResult."""
        pass

    @abc.abstractmethod
    def explain_query(self, query: str) -> str:
        """Return the EXPLAIN execution plan for the query."""
        pass

    @abc.abstractmethod
    def get_table_names(self) -> List[str]:
        """Return list of existing table names in the catalog."""
        pass

    @abc.abstractmethod
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """Return column names and types for a given table."""
        pass

    @staticmethod
    def compute_data_hash(df: pd.DataFrame) -> str:
        """Compute deterministic SHA-256 hash of tabular dataset."""
        serialized = df.to_json(orient="records", date_format="iso")
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_query_hash(query: str) -> str:
        """Compute deterministic SHA-256 hash of normalized SQL query."""
        normalized = " ".join(query.strip().lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
