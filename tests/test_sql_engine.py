"""Unit tests for SQL AST Validator, Generator, and Cost Estimator."""

import pytest
from core.semantic_layer.catalog import build_default_semantic_catalog
from core.sql_engine.validator import SQLValidator
from core.sql_engine.generator import GroundedSQLGenerator
from core.sql_engine.optimizer import QueryOptimizer
from warehouse.generator import create_in_memory_warehouse
from core.db.duckdb_engine import DuckDBEngine


@pytest.fixture(scope="module")
def catalog():
    return build_default_semantic_catalog()


@pytest.fixture(scope="module")
def db_con():
    return create_in_memory_warehouse(seed=42)


def test_sql_validator_syntax_error(catalog):
    """Verify syntax error is caught."""
    validator = SQLValidator(catalog)
    res = validator.validate("SELEC * FORM orders")
    assert res.is_valid is False
    assert any("Syntax Error" in e for e in res.errors)


def test_sql_validator_mutation_rejection(catalog):
    """Verify mutating queries are strictly rejected as not read-only."""
    validator = SQLValidator(catalog)
    
    # DROP
    res = validator.validate("DROP TABLE customers;")
    assert res.is_valid is False
    assert res.is_read_only is False
    assert any("Mutating statement" in e for e in res.errors)

    # DELETE
    res = validator.validate("DELETE FROM orders WHERE order_id = 1001;")
    assert res.is_valid is False
    assert res.is_read_only is False

    # UPDATE
    res = validator.validate("UPDATE customers SET segment = 'Enterprise';")
    assert res.is_valid is False

    # INSERT
    res = validator.validate("INSERT INTO customers (customer_id) VALUES (9999);")
    assert res.is_valid is False


def test_sql_validator_schema_validation(catalog):
    """Verify non-existent tables are rejected."""
    validator = SQLValidator(catalog)
    res = validator.validate("SELECT * FROM non_existent_table_xyz")
    assert res.is_valid is False
    assert any("not defined in the semantic catalog" in e for e in res.errors)


def test_sql_validator_pii_detection(catalog):
    """Verify PII column selected directly is rejected."""
    validator = SQLValidator(catalog)
    res = validator.validate("SELECT customer_id, credit_score FROM customers")
    assert res.is_valid is False
    assert res.pii_detected is True
    assert any("PII Policy violation" in e for e in res.errors)


def test_sql_validator_fanout_detection(catalog):
    """Verify join fanout calculation error is detected."""
    validator = SQLValidator(catalog)
    # Summing orders.total_amount after joining order_items duplicates order total by item count!
    query = """
    SELECT c.segment, SUM(o.total_amount)
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY c.segment;
    """
    res = validator.validate(query)
    assert res.is_valid is False
    assert res.fanout_risk is True
    assert any("Fanout calculation error" in e for e in res.errors)


def test_grounded_sql_generator_build_metric_query(catalog, db_con):
    """Verify grounded SQL generator constructs valid and executable SQL."""
    gen = GroundedSQLGenerator(catalog)
    sql = gen.build_metric_query(
        metric_name="revenue",
        dimensions=["segment", "quarter"],
        filters={"quarter": [2, 3]},
    )
    assert "SUM(order_items.net_amount) AS revenue" in sql
    assert "JOIN orders ON order_items.order_id = orders.order_id" in sql
    assert "JOIN customers ON orders.customer_id = customers.customer_id" in sql
    assert "GROUP BY customers.segment, calendar_dim.quarter" in sql

    # Validate with SQLValidator
    validator = SQLValidator(catalog)
    val_res = validator.validate(sql)
    assert val_res.is_valid is True

    # Execute on DuckDB
    engine = DuckDBEngine(connection=db_con)
    exec_res = engine.execute_query(sql)
    assert exec_res.row_count > 0
    assert "revenue" in exec_res.columns


def test_query_optimizer_cost_estimate(catalog, db_con):
    """Verify query cost estimation and EXPLAIN plan."""
    engine = DuckDBEngine(connection=db_con)
    optimizer = QueryOptimizer(cost_threshold=50000.0)

    query = "SELECT COUNT(*) FROM orders"
    est = optimizer.estimate_cost(query, engine)
    assert est.is_acceptable_cost is True
    assert est.estimated_cost >= 0
    assert len(est.explain_plan) > 0
