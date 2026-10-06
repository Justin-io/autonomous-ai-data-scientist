"""Grounded SQL Generator.

Synthesizes safe, schema-grounded SQL queries based on Semantic Layer definitions,
canonical metrics, dimensions, and allowable join paths.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from core.semantic_layer.catalog import SemanticCatalog
from core.semantic_layer.models import Metric, Dimension, Grain


class GroundedSQLGenerator:
    """Generates schema-grounded SQL queries using the semantic catalog."""

    def __init__(self, catalog: SemanticCatalog):
        self.catalog = catalog

    def build_metric_query(
        self,
        metric_name: str,
        dimensions: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Dict[str, str]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = 1000,
    ) -> str:
        """Construct grounded SQL query for a canonical metric and dimensions."""
        metric = self.catalog.resolve_metric(metric_name)
        if not metric:
            raise ValueError(f"Unknown metric '{metric_name}' in semantic catalog.")

        dimensions = dimensions or []
        resolved_dims: List[Dimension] = []
        for d in dimensions:
            dim_obj = self.catalog.resolve_dimension(d)
            if not dim_obj:
                raise ValueError(f"Unknown dimension '{d}' in semantic catalog.")
            resolved_dims.append(dim_obj)

        # Collect all required tables
        tables = [metric.base_table]
        for d in resolved_dims:
            if d.table_name not in tables:
                tables.append(d.table_name)

        # If date filtering on calendar_dim, ensure calendar_dim is included
        if date_range or (filters and any("date" in k or "quarter" in k or "year" in k for k in filters)):
            if "calendar_dim" not in tables:
                tables.append("calendar_dim")

        # In orders/order_items context, if joining order_items and calendar_dim, we must bridge through orders
        if "order_items" in tables and "calendar_dim" in tables and "orders" not in tables:
            tables.append("orders")
        if "order_items" in tables and "customers" in tables and "orders" not in tables:
            tables.append("orders")

        # Validate join path
        valid, err = self.catalog.validate_join_path(tables)
        if not valid:
            raise ValueError(f"Invalid join configuration: {err}")

        # Build SELECT clause
        select_parts = []
        for d in resolved_dims:
            select_parts.append(f"{d.table_name}.{d.column_name} AS {d.name}")
        select_parts.append(f"{metric.sql_expression} AS {metric.name}")
        select_clause = ", ".join(select_parts)

        # Build FROM & JOIN clauses
        # Determine base table
        base_table = metric.base_table
        # If orders is needed to bridge, ensure proper order
        join_clauses = self.catalog.get_join_clauses(tables, base_table=base_table)
        from_clause = f"FROM {base_table}\n" + "\n".join(join_clauses)

        # Build WHERE clause
        where_conditions = []
        if date_range:
            if "start" in date_range:
                where_conditions.append(f"calendar_dim.date_key >= '{date_range['start']}'")
            if "end" in date_range:
                where_conditions.append(f"calendar_dim.date_key <= '{date_range['end']}'")

        if filters:
            for col, val in filters.items():
                dim_match = self.catalog.resolve_dimension(col)
                if dim_match:
                    t_col = f"{dim_match.table_name}.{dim_match.column_name}"
                else:
                    t_col = col

                if isinstance(val, (list, tuple)):
                    vals_str = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in val)
                    where_conditions.append(f"{t_col} IN ({vals_str})")
                elif isinstance(val, str):
                    where_conditions.append(f"{t_col} = '{val}'")
                elif val is not None:
                    where_conditions.append(f"{t_col} = {val}")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Build GROUP BY clause
        group_clause = ""
        if resolved_dims:
            group_cols = [f"{d.table_name}.{d.column_name}" for d in resolved_dims]
            group_clause = "GROUP BY " + ", ".join(group_cols)

        # Build ORDER BY clause
        order_clause = ""
        if order_by:
            order_clause = f"ORDER BY {order_by}"
        elif resolved_dims:
            order_clause = f"ORDER BY {resolved_dims[0].name}"

        # Build LIMIT clause
        limit_clause = f"LIMIT {limit}" if limit else ""

        query = f"SELECT {select_clause}\n{from_clause}\n{where_clause}\n{group_clause}\n{order_clause}\n{limit_clause};"
        # Clean extra newlines
        lines = [line.strip() for line in query.split("\n") if line.strip()]
        return "\n".join(lines)

    def build_comparison_query(
        self,
        metric_name: str,
        period_dimension: str,
        period_a: Any,
        period_b: Any,
        segment_dimension: Optional[str] = None,
    ) -> str:
        """Construct grounded comparative analysis query between two periods."""
        dims = [period_dimension]
        if segment_dimension:
            dims.append(segment_dimension)

        filters = {period_dimension: [period_a, period_b]}
        return self.build_metric_query(
            metric_name=metric_name,
            dimensions=dims,
            filters=filters,
            order_by=f"{period_dimension}, {metric_name} DESC" if segment_dimension else period_dimension,
        )
