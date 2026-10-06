"""Benchmark Scenarios verification and metadata module."""

from __future__ import annotations

from typing import Dict, Any
import duckdb


class BenchmarkScenarios:
    """Provides ground-truth scenario validation queries and metadata."""

    @staticmethod
    def get_q3_revenue_decline_ground_truth(con: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
        """Verify BQ-1: Q3 vs Q2 revenue decline and Enterprise contribution."""
        query = """
        WITH quarterly AS (
            SELECT 
                c.fiscal_quarter,
                c.quarter,
                SUM(oi.net_amount) AS revenue,
                COUNT(DISTINCT o.order_id) AS order_count,
                AVG(oi.net_amount) AS avg_item_rev
            FROM orders o
            JOIN calendar_dim c ON o.order_date_only = c.date_key
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE c.year = 2024 AND c.quarter IN (2, 3)
            GROUP BY c.fiscal_quarter, c.quarter
            ORDER BY c.quarter
        )
        SELECT * FROM quarterly;
        """
        df = con.execute(query).df()
        q2_rev = float(df[df["quarter"] == 2]["revenue"].iloc[0])
        q3_rev = float(df[df["quarter"] == 3]["revenue"].iloc[0])
        diff_pct = ((q3_rev - q2_rev) / q2_rev) * 100.0

        # Segment breakdown
        segment_query = """
        SELECT 
            cu.segment,
            c.quarter,
            SUM(oi.net_amount) AS revenue
        FROM orders o
        JOIN customers cu ON o.customer_id = cu.customer_id
        JOIN calendar_dim c ON o.order_date_only = c.date_key
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE c.year = 2024 AND c.quarter IN (2, 3)
        GROUP BY cu.segment, c.quarter
        ORDER BY cu.segment, c.quarter;
        """
        seg_df = con.execute(segment_query).df()
        
        return {
            "q2_revenue": round(q2_rev, 2),
            "q3_revenue": round(q3_rev, 2),
            "decline_percentage": round(diff_pct, 2),
            "segment_df": seg_df,
        }

    @staticmethod
    def get_simpsons_paradox_ground_truth(con: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
        """Verify BQ-2: Simpson's paradox in checkout A/B test."""
        # 1. Aggregate View
        agg_query = """
        SELECT 
            variant,
            COUNT(*) AS sessions,
            SUM(CASE WHEN converted THEN 1 ELSE 0 END) AS conversions,
            AVG(CASE WHEN converted THEN 1.0 ELSE 0.0 END) AS conversion_rate
        FROM ab_test_checkout
        GROUP BY variant
        ORDER BY variant;
        """
        agg_df = con.execute(agg_query).df()

        # 2. Stratified Subgroup View (by Device)
        strat_query = """
        SELECT 
            variant,
            device,
            COUNT(*) AS sessions,
            SUM(CASE WHEN converted THEN 1 ELSE 0 END) AS conversions,
            AVG(CASE WHEN converted THEN 1.0 ELSE 0.0 END) AS conversion_rate
        FROM ab_test_checkout
        GROUP BY variant, device
        ORDER BY device, variant;
        """
        strat_df = con.execute(strat_query).df()

        return {
            "aggregate": agg_df,
            "stratified": strat_df,
            "is_simpsons_paradox": True,
        }

    @staticmethod
    def get_august_refund_surge_ground_truth(con: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
        """Verify BQ-3: August defect refund spike."""
        query = """
        SELECT 
            c.month,
            c.month_name,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COUNT(DISTINCT r.refund_id) AS total_refunds,
            ROUND(COUNT(DISTINCT r.refund_id) * 100.0 / COUNT(DISTINCT o.order_id), 2) AS refund_rate_pct
        FROM orders o
        JOIN calendar_dim c ON o.order_date_only = c.date_key
        LEFT JOIN refunds r ON o.order_id = r.order_id
        WHERE c.year = 2024 AND c.month IN (6, 7, 8, 9)
        GROUP BY c.month, c.month_name
        ORDER BY c.month;
        """
        df = con.execute(query).df()
        return {"monthly_refund_rates": df}
