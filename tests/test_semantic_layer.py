"""Unit tests for Semantic Layer catalog, metrics, and join path resolution."""

import pytest
from core.semantic_layer.catalog import build_default_semantic_catalog
from core.semantic_layer.models import Grain, MetricType


def test_semantic_catalog_loading():
    """Verify default semantic catalog loads all canonical entities and metrics."""
    catalog = build_default_semantic_catalog()

    assert "customers" in catalog.entities
    assert "orders" in catalog.entities
    assert "order_items" in catalog.entities
    assert "revenue" in catalog.metrics
    assert "order_count" in catalog.metrics
    assert "aov" in catalog.metrics
    assert "churn_rate" in catalog.metrics
    assert "refund_rate" in catalog.metrics


def test_metric_synonym_resolution():
    """Verify natural language terms resolve to canonical metrics."""
    catalog = build_default_semantic_catalog()

    assert catalog.resolve_metric("sales").name == "revenue"
    assert catalog.resolve_metric("total_revenue").name == "revenue"
    assert catalog.resolve_metric("transactions").name == "order_count"
    assert catalog.resolve_metric("average_order_value").name == "aov"
    assert catalog.resolve_metric("return_rate").name == "refund_rate"


def test_dimension_resolution():
    """Verify dimensions resolve correctly."""
    catalog = build_default_semantic_catalog()

    assert catalog.resolve_dimension("tier").name == "segment"
    assert catalog.resolve_dimension("geography").name == "country"
    assert catalog.resolve_dimension("product_category").name == "category"


def test_allowable_join_path_validation():
    """Verify valid and invalid join paths are caught."""
    catalog = build_default_semantic_catalog()

    # Valid multi-table join path: order_items -> orders -> customers
    valid, err = catalog.validate_join_path(["order_items", "orders", "customers"])
    assert valid is True
    assert err is None

    # Valid join path with calendar: order_items -> orders -> calendar_dim
    valid, err = catalog.validate_join_path(["order_items", "orders", "calendar_dim"])
    assert valid is True

    # Disconnected join path (would create cartesian fanout)
    valid, err = catalog.validate_join_path(["order_items", "subscriptions"])
    assert valid is False
    assert "Cartesian product" in err


def test_join_clause_generation():
    """Verify automatic allowable join clauses."""
    catalog = build_default_semantic_catalog()
    clauses = catalog.get_join_clauses(["orders", "customers", "calendar_dim"], base_table="orders")
    assert len(clauses) == 2
    assert any("JOIN customers" in c for c in clauses)
    assert any("JOIN calendar_dim" in c for c in clauses)
