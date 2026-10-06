"""Unit tests for Warehouse generation and benchmark scenarios."""

import pytest
import duckdb
from warehouse.generator import WarehouseGenerator, create_in_memory_warehouse
from warehouse.scenarios import BenchmarkScenarios
from core.db.duckdb_engine import DuckDBEngine


@pytest.fixture(scope="module")
def db_con():
    """Create in-memory warehouse once for all tests in module."""
    return create_in_memory_warehouse(seed=42)


def test_warehouse_generation_table_counts(db_con):
    """Verify all 10 relational tables are generated with non-zero row counts."""
    tables = [r[0] for r in db_con.execute("SHOW TABLES").fetchall()]
    expected_tables = [
        "calendar_dim",
        "customers",
        "products",
        "marketing_channels",
        "orders",
        "order_items",
        "subscriptions",
        "payments",
        "refunds",
        "ab_test_checkout",
    ]
    for table in expected_tables:
        assert table in tables, f"Table {table} missing from warehouse"
        cnt = db_con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert cnt > 0, f"Table {table} has 0 rows"


def test_q3_revenue_decline_scenario(db_con):
    """Verify BQ-1 scenario exhibits ~7.5% - 8.5% revenue decline from Q2 to Q3."""
    gt = BenchmarkScenarios.get_q3_revenue_decline_ground_truth(db_con)

    assert gt["q2_revenue"] > 0
    assert gt["q3_revenue"] > 0
    assert -12.0 <= gt["decline_percentage"] <= -5.0, (
        f"Expected Q3 decline around -8%, got {gt['decline_percentage']}%"
    )

    # Check that Enterprise segment accounts for disproportionate drop
    seg_df = gt["segment_df"]
    q2_ent = float(seg_df[(seg_df["segment"] == "Enterprise") & (seg_df["quarter"] == 2)]["revenue"].iloc[0])
    q3_ent = float(seg_df[(seg_df["segment"] == "Enterprise") & (seg_df["quarter"] == 3)]["revenue"].iloc[0])
    ent_drop = q2_ent - q3_ent
    assert ent_drop > 0, "Enterprise revenue should drop in Q3"


def test_simpsons_paradox_scenario(db_con):
    """Verify BQ-2 exhibits true Simpson's paradox between aggregate and stratified views."""
    gt = BenchmarkScenarios.get_simpsons_paradox_ground_truth(db_con)

    agg = gt["aggregate"].set_index("variant")
    cvr_a_agg = agg.loc["control_A", "conversion_rate"]
    cvr_b_agg = agg.loc["treatment_B", "conversion_rate"]

    # In aggregate, Variant B appears higher
    assert cvr_b_agg > cvr_a_agg, "Aggregate treatment B must appear higher than A"

    # In stratified view by device, Variant A is strictly superior for both desktop and mobile
    strat = gt["stratified"].set_index(["device", "variant"])
    assert strat.loc[("desktop", "control_A"), "conversion_rate"] > strat.loc[("desktop", "treatment_B"), "conversion_rate"]
    assert strat.loc[("mobile", "control_A"), "conversion_rate"] > strat.loc[("mobile", "treatment_B"), "conversion_rate"]


def test_august_refund_surge_scenario(db_con):
    """Verify BQ-3 exhibits August refund surge."""
    gt = BenchmarkScenarios.get_august_refund_surge_ground_truth(db_con)
    df = gt["monthly_refund_rates"].set_index("month")

    june_rate = float(df.loc[6, "refund_rate_pct"])
    july_rate = float(df.loc[7, "refund_rate_pct"])
    aug_rate = float(df.loc[8, "refund_rate_pct"])

    assert aug_rate > 10.0, f"August refund rate should be > 10%, got {aug_rate}%"
    assert aug_rate > (june_rate * 4.0), "August refund rate should surge >4x vs baseline"


def test_duckdb_engine_read_only_enforcement(db_con):
    """Verify DuckDBEngine executes read queries but raises on mutation."""
    engine = DuckDBEngine(connection=db_con)

    # Valid read query
    result = engine.execute_query("SELECT COUNT(*) AS total FROM customers")
    assert result.row_count == 1
    assert result.rows[0]["total"] > 0
    assert len(result.data_hash) == 64

    # Malicious mutating query
    with pytest.raises(PermissionError):
        engine.execute_query("DROP TABLE customers")

    with pytest.raises(PermissionError):
        engine.execute_query("DELETE FROM customers WHERE customer_id = 1")
