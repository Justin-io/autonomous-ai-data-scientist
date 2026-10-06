"""DuckDB In-Process Analytical Engine Implementation."""

from __future__ import annotations

import time
from typing import Dict, List, Optional
import duckdb
import pandas as pd

from core.db.connector import DatabaseEngine, ExecutionResult


class DuckDBEngine(DatabaseEngine):
    """DuckDB columnar analytical engine."""

    def __init__(self, connection: Optional[duckdb.DuckDBPyConnection] = None, database_path: str = ":memory:"):
        if connection is not None:
            self.con = connection
        else:
            self.con = duckdb.connect(database=database_path)

    def execute_query(
        self,
        query: str,
        max_rows: int = 10000,
        timeout_seconds: float = 30.0,
    ) -> ExecutionResult:
        """Execute analytical query against DuckDB."""
        # Enforce read-only check (first layer of defense)
        normalized = query.strip().lower()
        forbidden_keywords = ["drop ", "delete ", "insert ", "update ", "alter ", "create ", "grant ", "truncate "]
        for kw in forbidden_keywords:
            if kw in normalized:
                raise PermissionError(f"Security violation: statement contains forbidden mutation keyword '{kw.strip()}'.")

        start_time = time.perf_counter()
        
        # Execute query
        rel = self.con.execute(query)
        df: pd.DataFrame = rel.fetchdf()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        truncated = False
        if len(df) > max_rows:
            df = df.iloc[:max_rows]
            truncated = True

        data_hash = self.compute_data_hash(df)
        query_hash = self.compute_query_hash(query)

        # Convert datetimes / Timestamps to ISO strings for clean JSON serialization
        rows = df.to_dict(orient="records")
        for row in rows:
            for k, v in row.items():
                if isinstance(v, (pd.Timestamp, pd.Period)):
                    row[k] = str(v)

        return ExecutionResult(
            columns=list(df.columns),
            rows=rows,
            row_count=len(df),
            execution_time_ms=round(elapsed_ms, 2),
            query_hash=query_hash,
            data_hash=data_hash,
            truncated=truncated,
        )

    def explain_query(self, query: str) -> str:
        """Return the EXPLAIN execution plan for the query."""
        plan_df = self.con.execute(f"EXPLAIN {query}").fetchdf()
        return "\n".join(plan_df.iloc[:, 0].astype(str).tolist())

    def get_table_names(self) -> List[str]:
        """Return list of existing table names in the catalog."""
        res = self.con.execute("SHOW TABLES").fetchall()
        return [r[0] for r in res]

    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """Return column names and types for a given table."""
        res = self.con.execute(f"DESCRIBE {table_name}").fetchall()
        return {r[0]: str(r[1]) for r in res}
