"""SQL AST Validator, Read-Only Enforcer, and Fanout Guard."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
import sqlglot
from sqlglot import exp

from core.semantic_layer.catalog import SemanticCatalog


class SQLValidationResult(BaseModel):
    """Result of AST and semantic SQL validation."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    tables_referenced: List[str] = Field(default_factory=list)
    columns_referenced: List[str] = Field(default_factory=list)
    has_aggregations: bool = False
    has_group_by: bool = False
    is_read_only: bool = True
    pii_detected: bool = False
    fanout_risk: bool = False
    suggested_sql: Optional[str] = None


class SQLValidator:
    """Robust AST validator enforcing schema, read-only, grain, fanout, and PII safety."""

    def __init__(self, catalog: Optional[SemanticCatalog] = None):
        self.catalog = catalog

    def validate(self, sql: str) -> SQLValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        tables: List[str] = []
        columns: List[str] = []
        has_agg = False
        has_group = False
        is_read_only = True
        pii_detected = False
        fanout_risk = False

        # 1. Syntax Parsing
        try:
            parsed = sqlglot.parse_one(sql)
        except Exception as e:
            return SQLValidationResult(
                is_valid=False,
                errors=[f"SQL Syntax Error: {str(e)}"],
                is_read_only=False,
            )

        # 2. Read-Only AST Enforcement
        disallowed_classes = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Create,
            exp.Alter,
            exp.Command,
            exp.Grant,
            exp.Pragma,
        )
        for node in parsed.walk():
            if isinstance(node, disallowed_classes):
                is_read_only = False
                errors.append(f"Security violation: Mutating statement {node.__class__.__name__} detected.")

        if not isinstance(parsed, (exp.Select, exp.Union)):
            is_read_only = False
            errors.append(f"SQL Syntax Error: Root AST node must be SELECT or UNION, got {parsed.__class__.__name__}.")

        # 3. Table Extraction and Schema Validation
        raw_tables = [t.name.lower() for t in parsed.find_all(exp.Table) if t.name]
        tables = list(dict.fromkeys(raw_tables))  # Deduplicate preserving order

        # Build alias to table map
        alias_map: Dict[str, str] = {}
        for t in parsed.find_all(exp.Table):
            if t.name:
                t_lower = t.name.lower()
                alias_map[t_lower] = t_lower
                if t.alias:
                    alias_map[t.alias.lower()] = t_lower

        # Ignore common CTE names
        ctes = set()
        for with_expr in parsed.find_all(exp.With):
            for cte in with_expr.expressions:
                if cte.alias:
                    ctes.add(cte.alias.lower())

        base_tables = [t for t in tables if t not in ctes]

        if self.catalog:
            for t in base_tables:
                if t not in self.catalog.entities:
                    errors.append(f"Schema violation: Table '{t}' is not defined in the semantic catalog.")

        # 4. Join Cardinality & Fanout Detection
        if self.catalog and len(base_tables) > 1:
            valid_path, path_err = self.catalog.validate_join_path(base_tables)
            if not valid_path:
                fanout_risk = True
                errors.append(f"Join fanout risk: {path_err}")

            # Specific fanout check: joining orders and order_items without aggregating order_items first
            if "orders" in base_tables and "order_items" in base_tables:
                # If orders.total_amount is summed directly when joined to order_items, each order row is duplicated per item!
                for col_node in parsed.find_all(exp.Column):
                    t_qualifier = col_node.table.lower() if col_node.table else None
                    actual_tbl = alias_map.get(t_qualifier, t_qualifier)
                    if col_node.name.lower() in ["total_amount", "discount_amount"] and (actual_tbl == "orders" or actual_tbl is None):
                        parent_sum = col_node.find_ancestor(exp.Sum, exp.Avg)
                        if parent_sum:
                            fanout_risk = True
                            errors.append(
                                "Fanout calculation error: Aggregating 'orders.total_amount' across a 1:N join with 'order_items' "
                                "causes multiplication by item count. Use 'SUM(order_items.net_amount)' instead."
                            )

        # 5. Column Extraction & PII Enforcement
        for col in parsed.find_all(exp.Column):
            col_name = col.name.lower()
            t_qualifier = col.table.lower() if col.table else None
            table_name = alias_map.get(t_qualifier, t_qualifier)
            columns.append(col_name)

            if self.catalog:
                # Check for PII column
                for ent_name, ent in self.catalog.entities.items():
                    if table_name and ent.table_name != table_name:
                        continue
                    if col_name in ent.columns:
                        col_meta = ent.columns[col_name]
                        if col_meta.pii:
                            # Check if column is raw in select or aggregated
                            ancestor_agg = col.find_ancestor(exp.Count, exp.Min, exp.Max)
                            if not ancestor_agg:
                                pii_detected = True
                                errors.append(f"PII Policy violation: Column '{col_name}' contains sensitive PII and cannot be selected in plaintext.")

        # 6. Aggregations & Group By Grain Validation
        agg_functions = (exp.Sum, exp.Avg, exp.Count, exp.Min, exp.Max)
        has_agg = any(isinstance(node, agg_functions) for node in parsed.walk())
        has_group = parsed.find(exp.Group) is not None

        # 7. Denominator Zero Division Validation
        for div_op in parsed.find_all(exp.Div):
            # Check right operand
            right = div_op.this
            # Look for nullif
            if not isinstance(right, exp.Nullif) and not "nullif" in right.sql().lower():
                warnings.append(f"Denominator safety: Division expression '{div_op.sql()}' does not wrap denominator in NULLIF(..., 0). Risk of division by zero.")

        # 8. Date Boundary Check
        # Check if calendar_dim or order_date is referenced with WHERE clause
        has_where = parsed.find(exp.Where) is not None
        if not has_where and any(t in ["orders", "order_items", "payments", "refunds"] for t in base_tables):
            warnings.append("Performance warning: Query scans transactional tables without an explicit WHERE date boundary.")

        is_valid = (len(errors) == 0) and is_read_only

        return SQLValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            tables_referenced=base_tables,
            columns_referenced=list(dict.fromkeys(columns)),
            has_aggregations=has_agg,
            has_group_by=has_group,
            is_read_only=is_read_only,
            pii_detected=pii_detected,
            fanout_risk=fanout_risk,
        )
