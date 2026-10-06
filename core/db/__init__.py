"""Database connector module for Autonomous AI Data Scientist."""

from core.db.connector import DatabaseEngine, ExecutionResult
from core.db.duckdb_engine import DuckDBEngine
from core.db.postgres_engine import PostgreSQLEngine

__all__ = [
    "DatabaseEngine",
    "ExecutionResult",
    "DuckDBEngine",
    "PostgreSQLEngine",
]
