"""PostgreSQL Engine Connector Implementation."""

from __future__ import annotations

import time
from typing import Dict, List, Optional
import pandas as pd
from sqlalchemy import create_engine, text

from core.db.connector import DatabaseEngine, ExecutionResult


class PostgreSQLEngine(DatabaseEngine):
    """PostgreSQL read-only analytical engine connector."""

    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.engine = create_engine(
            connection_url,
            pool_pre_ping=True,
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )

    def execute_query(
        self,
        query: str,
        max_rows: int = 10000,
        timeout_seconds: float = 30.0,
    ) -> ExecutionResult:
        """Execute read-only query against PostgreSQL."""
        normalized = query.strip().lower()
        forbidden_keywords = ["drop ", "delete ", "insert ", "update ", "alter ", "create ", "grant ", "truncate "]
        for kw in forbidden_keywords:
            if kw in normalized:
                raise PermissionError(f"Security violation: statement contains forbidden mutation keyword '{kw.strip()}'.")

        start_time = time.perf_counter()
        with self.engine.connect() as conn:
            # Set statement timeout
            conn.execute(text(f"SET statement_timeout = {int(timeout_seconds * 1000)}"))
            # Enforce read-only transaction mode
            conn.execute(text("SET TRANSACTION READ ONLY"))
            
            result = conn.execute(text(query))
            keys = list(result.keys())
            rows_data = result.fetchmany(max_rows + 1)
            
            truncated = len(rows_data) > max_rows
            if truncated:
                rows_data = rows_data[:max_rows]

            df = pd.DataFrame(rows_data, columns=keys)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        data_hash = self.compute_data_hash(df)
        query_hash = self.compute_query_hash(query)

        rows = df.to_dict(orient="records")
        return ExecutionResult(
            columns=keys,
            rows=rows,
            row_count=len(df),
            execution_time_ms=round(elapsed_ms, 2),
            query_hash=query_hash,
            data_hash=data_hash,
            truncated=truncated,
        )

    def explain_query(self, query: str) -> str:
        """Return PostgreSQL EXPLAIN plan."""
        with self.engine.connect() as conn:
            res = conn.execute(text(f"EXPLAIN {query}")).fetchall()
            return "\n".join(r[0] for r in res)

    def get_table_names(self) -> List[str]:
        """Fetch tables in the public schema."""
        with self.engine.connect() as conn:
            query = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            res = conn.execute(query).fetchall()
            return [r[0] for r in res]

    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """Fetch column names and types for a table."""
        with self.engine.connect() as conn:
            query = text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = :tname"
            )
            res = conn.execute(query, {"tname": table_name}).fetchall()
            return {r[0]: r[1] for r in res}
