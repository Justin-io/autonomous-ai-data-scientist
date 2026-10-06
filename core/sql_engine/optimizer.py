"""SQL Query Cost Estimator, Optimizer, and Cache."""

from __future__ import annotations

import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field

from core.db.connector import DatabaseEngine, ExecutionResult


class QueryCostEstimate(BaseModel):
    """Cost estimation and execution plan metadata."""

    estimated_cost: float
    estimated_rows: int
    is_acceptable_cost: bool
    exceeds_threshold: bool
    explain_plan: str
    recommendations: List[str] = Field(default_factory=list)


class QueryOptimizer:
    """Estimates query cost, validates execution thresholds, and caches results."""

    def __init__(self, cost_threshold: float = 100000.0, max_row_threshold: int = 500000):
        self.cost_threshold = cost_threshold
        self.max_row_threshold = max_row_threshold
        self._cache: Dict[str, ExecutionResult] = {}

    def estimate_cost(self, query: str, engine: DatabaseEngine) -> QueryCostEstimate:
        """Run EXPLAIN query on database engine to estimate cost and complexity."""
        try:
            explain_text = engine.explain_query(query)
        except Exception as e:
            return QueryCostEstimate(
                estimated_cost=0.0,
                estimated_rows=0,
                is_acceptable_cost=True,
                exceeds_threshold=False,
                explain_plan=f"Could not retrieve EXPLAIN plan: {str(e)}",
                recommendations=["Proceed with caution as execution plan was unavailable."],
            )

        # Parse DuckDB or Postgres explain plan
        # DuckDB plan includes: e.g. "EC: 1000" (Estimated Cardinality)
        estimated_rows = 1000
        ec_match = re.search(r"EC:\s*([0-9]+)", explain_text)
        if ec_match:
            estimated_rows = int(ec_match.group(1))
        else:
            # Look for Postgres style: rows=1234
            rows_match = re.search(r"rows=([0-9]+)", explain_text)
            if rows_match:
                estimated_rows = int(rows_match.group(1))

        # Relative cost proxy
        cost_match = re.search(r"cost=[0-9.]+\.\.([0-9.]+)", explain_text)
        if cost_match:
            estimated_cost = float(cost_match.group(1))
        else:
            # DuckDB heuristic based on estimated rows and join count
            join_count = len(re.findall(r"JOIN", query, re.IGNORECASE))
            estimated_cost = float(estimated_rows * (1.0 + 0.5 * join_count))

        exceeds = (estimated_cost > self.cost_threshold) or (estimated_rows > self.max_row_threshold)
        recommendations = []
        if exceeds:
            recommendations.append(
                f"Query cost {estimated_cost:.0f} or row count {estimated_rows} exceeds safety threshold. "
                "Consider pushing down date predicates or restricting dimensions."
            )
        if "seq scan" in explain_text.lower():
            recommendations.append("Sequential scan detected. Adding index or partition pruning may improve performance.")

        return QueryCostEstimate(
            estimated_cost=round(estimated_cost, 2),
            estimated_rows=estimated_rows,
            is_acceptable_cost=not exceeds,
            exceeds_threshold=exceeds,
            explain_plan=explain_text,
            recommendations=recommendations,
        )

    def get_cached_result(self, query_hash: str) -> Optional[ExecutionResult]:
        """Retrieve cached execution result if available."""
        return self._cache.get(query_hash)

    def store_cached_result(self, query_hash: str, result: ExecutionResult) -> None:
        """Store query execution result in cache."""
        self._cache[query_hash] = result

    def clear_cache(self) -> None:
        """Clear query cache."""
        self._cache.clear()
