"""Semantic Layer Catalog Implementation.

Provides canonical business entities, metrics, dimensions, relationships,
synonym resolution, and allowable join path validation.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set
from pydantic import BaseModel, Field

from core.semantic_layer.models import (
    Entity,
    Metric,
    Dimension,
    Relationship,
    ColumnMetadata,
    Grain,
    MetricType,
    DimensionType,
    RelationshipType,
)


class SemanticCatalog(BaseModel):
    """Complete enterprise semantic catalog."""

    entities: Dict[str, Entity] = Field(default_factory=dict)
    metrics: Dict[str, Metric] = Field(default_factory=dict)
    dimensions: Dict[str, Dimension] = Field(default_factory=dict)
    relationships: List[Relationship] = Field(default_factory=list)

    def resolve_metric(self, term: str) -> Optional[Metric]:
        """Resolve a natural language term or metric key to a canonical Metric."""
        clean_term = term.strip().lower().replace(" ", "_")
        if clean_term in self.metrics:
            return self.metrics[clean_term]
        
        # Check synonyms
        for m in self.metrics.values():
            if clean_term == m.name.lower():
                return m
            if any(clean_term == s.lower().replace(" ", "_") for s in m.synonyms):
                return m
            if clean_term in m.name.lower() or clean_term in m.display_name.lower():
                return m
        return None

    def resolve_dimension(self, term: str) -> Optional[Dimension]:
        """Resolve a natural language term or dimension key to a canonical Dimension."""
        clean_term = term.strip().lower().replace(" ", "_")
        if clean_term in self.dimensions:
            return self.dimensions[clean_term]
        
        for d in self.dimensions.values():
            if clean_term == d.name.lower() or clean_term == d.column_name.lower():
                return d
            if any(clean_term == s.lower().replace(" ", "_") for s in d.synonyms):
                return d
            if clean_term in d.name.lower():
                return d
        return None

    def get_relationship(self, table_a: str, table_b: str) -> Optional[Relationship]:
        """Find allowed relationship between two tables in either direction."""
        for r in self.relationships:
            if (r.from_table == table_a and r.to_table == table_b) or (
                r.from_table == table_b and r.to_table == table_a
            ):
                return r
        return None

    def validate_join_path(self, tables: List[str]) -> Tuple[bool, Optional[str]]:
        """Verify that all requested tables can be connected via allowable join paths."""
        if len(tables) <= 1:
            return True, None

        # Build adjacency graph
        adj: Dict[str, Set[str]] = {t: set() for t in tables}
        for r in self.relationships:
            if r.from_table in tables and r.to_table in tables and r.allowed:
                adj[r.from_table].add(r.to_table)
                adj[r.to_table].add(r.from_table)

        # BFS connectivity check
        visited = set()
        start = tables[0]
        queue = [start]
        visited.add(start)

        while queue:
            curr = queue.pop(0)
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if len(visited) != len(tables):
            unreachable = set(tables) - visited
            return (
                False,
                f"Disallowed or disconnected join path. Unreachable tables: {list(unreachable)}. "
                "Cartesian product would result.",
            )

        return True, None

    def get_join_clauses(self, tables: List[str], base_table: str) -> List[str]:
        """Return the minimal set of allowable JOIN SQL clauses to connect all tables."""
        if len(tables) <= 1:
            return []

        joined_tables = {base_table}
        clauses = []
        remaining = [t for t in tables if t != base_table]

        while remaining:
            progress = False
            for t in list(remaining):
                # Look for a relationship connecting t to an already joined table
                for j in joined_tables:
                    rel = self.get_relationship(t, j)
                    if rel and rel.allowed:
                        clauses.append(rel.join_clause)
                        joined_tables.add(t)
                        remaining.remove(t)
                        progress = True
                        break
                if progress:
                    break
            if not progress:
                break
        return clauses


def build_default_semantic_catalog() -> SemanticCatalog:
    """Build canonical enterprise semantic catalog."""
    catalog = SemanticCatalog()

    # 1. Entities
    catalog.entities["customers"] = Entity(
        name="Customer",
        table_name="customers",
        primary_key="customer_id",
        description="Enterprise and retail account holders.",
        grain=Grain.CUSTOMER,
        freshness="realtime",
        columns={
            "customer_id": ColumnMetadata(name="customer_id", data_type="INTEGER", is_primary_key=True),
            "created_at": ColumnMetadata(name="created_at", data_type="TIMESTAMP"),
            "segment": ColumnMetadata(
                name="segment",
                data_type="VARCHAR",
                description="Account tier: Enterprise, Mid-Market, SMB, Consumer",
                synonyms=["tier", "customer_tier", "client_segment"],
            ),
            "country": ColumnMetadata(name="country", data_type="VARCHAR", synonyms=["nation", "geography"]),
            "industry": ColumnMetadata(name="industry", data_type="VARCHAR", synonyms=["sector"]),
            "credit_score": ColumnMetadata(name="credit_score", data_type="INTEGER", pii=True),
            "is_active": ColumnMetadata(name="is_active", data_type="BOOLEAN"),
        },
        caveats=["Credit score contains PII and is restricted from raw display."],
    )

    catalog.entities["products"] = Entity(
        name="Product",
        table_name="products",
        primary_key="product_id",
        description="Catalog of software products, addons, and subscriptions.",
        grain=Grain.PRODUCT,
        columns={
            "product_id": ColumnMetadata(name="product_id", data_type="INTEGER", is_primary_key=True),
            "name": ColumnMetadata(name="name", data_type="VARCHAR"),
            "category": ColumnMetadata(
                name="category",
                data_type="VARCHAR",
                description="Product line: Core Platform, Pro Tools, Enterprise Addon, API Services",
                synonyms=["product_category", "product_line"],
            ),
            "base_price": ColumnMetadata(name="base_price", data_type="FLOAT"),
            "cost": ColumnMetadata(name="cost", data_type="FLOAT"),
        },
    )

    catalog.entities["marketing_channels"] = Entity(
        name="MarketingChannel",
        table_name="marketing_channels",
        primary_key="channel_id",
        description="Customer acquisition channels.",
        grain=Grain.CUSTOMER,
        columns={
            "channel_id": ColumnMetadata(name="channel_id", data_type="INTEGER", is_primary_key=True),
            "channel_name": ColumnMetadata(name="channel_name", data_type="VARCHAR", synonyms=["channel", "source"]),
            "acquisition_cost_tier": ColumnMetadata(name="acquisition_cost_tier", data_type="VARCHAR"),
        },
    )

    catalog.entities["orders"] = Entity(
        name="Order",
        table_name="orders",
        primary_key="order_id",
        description="Customer commercial transaction headers.",
        grain=Grain.ORDER,
        columns={
            "order_id": ColumnMetadata(name="order_id", data_type="INTEGER", is_primary_key=True),
            "customer_id": ColumnMetadata(name="customer_id", data_type="INTEGER", is_foreign_key=True, references_table="customers"),
            "channel_id": ColumnMetadata(name="channel_id", data_type="INTEGER", is_foreign_key=True, references_table="marketing_channels"),
            "order_date": ColumnMetadata(name="order_date", data_type="TIMESTAMP"),
            "order_date_only": ColumnMetadata(name="order_date_only", data_type="DATE", is_foreign_key=True, references_table="calendar_dim"),
            "status": ColumnMetadata(name="status", data_type="VARCHAR"),
            "device": ColumnMetadata(name="device", data_type="VARCHAR", synonyms=["device_type", "platform"]),
            "discount_amount": ColumnMetadata(name="discount_amount", data_type="FLOAT"),
            "shipping_amount": ColumnMetadata(name="shipping_amount", data_type="FLOAT"),
            "total_amount": ColumnMetadata(name="total_amount", data_type="FLOAT", synonyms=["gross_revenue", "order_value"]),
        },
    )

    catalog.entities["order_items"] = Entity(
        name="OrderItem",
        table_name="order_items",
        primary_key="item_id",
        description="Line-item detail for each order.",
        grain=Grain.ORDER_ITEM,
        columns={
            "item_id": ColumnMetadata(name="item_id", data_type="INTEGER", is_primary_key=True),
            "order_id": ColumnMetadata(name="order_id", data_type="INTEGER", is_foreign_key=True, references_table="orders"),
            "product_id": ColumnMetadata(name="product_id", data_type="INTEGER", is_foreign_key=True, references_table="products"),
            "quantity": ColumnMetadata(name="quantity", data_type="INTEGER"),
            "unit_price": ColumnMetadata(name="unit_price", data_type="FLOAT"),
            "net_amount": ColumnMetadata(name="net_amount", data_type="FLOAT", synonyms=["net_revenue", "sales"]),
        },
    )

    catalog.entities["subscriptions"] = Entity(
        name="Subscription",
        table_name="subscriptions",
        primary_key="subscription_id",
        description="Recurring SaaS customer subscriptions.",
        grain=Grain.SUBSCRIPTION,
        columns={
            "subscription_id": ColumnMetadata(name="subscription_id", data_type="INTEGER", is_primary_key=True),
            "customer_id": ColumnMetadata(name="customer_id", data_type="INTEGER", is_foreign_key=True, references_table="customers"),
            "plan_tier": ColumnMetadata(name="plan_tier", data_type="VARCHAR"),
            "status": ColumnMetadata(name="status", data_type="VARCHAR", synonyms=["subscription_status"]),
            "start_date": ColumnMetadata(name="start_date", data_type="DATE"),
            "end_date": ColumnMetadata(name="end_date", data_type="DATE"),
            "monthly_price": ColumnMetadata(name="monthly_price", data_type="FLOAT"),
            "mrr": ColumnMetadata(name="mrr", data_type="FLOAT"),
        },
    )

    catalog.entities["refunds"] = Entity(
        name="Refund",
        table_name="refunds",
        primary_key="refund_id",
        description="Processed refunds and chargebacks.",
        grain=Grain.REFUND,
        columns={
            "refund_id": ColumnMetadata(name="refund_id", data_type="INTEGER", is_primary_key=True),
            "order_id": ColumnMetadata(name="order_id", data_type="INTEGER", is_foreign_key=True, references_table="orders"),
            "refund_date": ColumnMetadata(name="refund_date", data_type="TIMESTAMP"),
            "amount": ColumnMetadata(name="amount", data_type="FLOAT"),
            "reason": ColumnMetadata(name="reason", data_type="VARCHAR"),
        },
    )

    catalog.entities["calendar_dim"] = Entity(
        name="Calendar",
        table_name="calendar_dim",
        primary_key="date_key",
        description="Canonical calendar and fiscal time dimension.",
        grain=Grain.DAY,
        columns={
            "date_key": ColumnMetadata(name="date_key", data_type="DATE", is_primary_key=True),
            "year": ColumnMetadata(name="year", data_type="INTEGER"),
            "quarter": ColumnMetadata(name="quarter", data_type="INTEGER"),
            "month": ColumnMetadata(name="month", data_type="INTEGER"),
            "month_name": ColumnMetadata(name="month_name", data_type="VARCHAR"),
            "day": ColumnMetadata(name="day", data_type="INTEGER"),
            "day_of_week": ColumnMetadata(name="day_of_week", data_type="INTEGER"),
            "is_weekend": ColumnMetadata(name="is_weekend", data_type="BOOLEAN"),
            "fiscal_quarter": ColumnMetadata(name="fiscal_quarter", data_type="VARCHAR"),
        },
    )

    # 2. Metrics
    catalog.metrics["revenue"] = Metric(
        name="revenue",
        display_name="Total Net Revenue",
        description="Sum of net amount across order items, accounting for quantity and item price.",
        metric_type=MetricType.SUM,
        sql_expression="SUM(order_items.net_amount)",
        base_table="order_items",
        grain=Grain.ORDER_ITEM,
        unit="USD",
        synonyms=["total_revenue", "sales", "net_revenue", "topline"],
        caveats=["To analyze revenue over calendar time, join order_items -> orders -> calendar_dim."],
    )

    catalog.metrics["order_count"] = Metric(
        name="order_count",
        display_name="Total Orders",
        description="Count of distinct completed orders.",
        metric_type=MetricType.COUNT_DISTINCT,
        sql_expression="COUNT(DISTINCT orders.order_id)",
        base_table="orders",
        grain=Grain.ORDER,
        unit="count",
        synonyms=["orders", "volume", "order_volume", "transactions"],
    )

    catalog.metrics["aov"] = Metric(
        name="aov",
        display_name="Average Order Value",
        description="Total revenue divided by count of distinct orders.",
        metric_type=MetricType.RATIO,
        sql_expression="SUM(orders.total_amount) / NULLIF(COUNT(DISTINCT orders.order_id), 0)",
        base_table="orders",
        grain=Grain.ORDER,
        unit="USD",
        denominator_metric="order_count",
        synonyms=["average_order_value", "mean_order_size", "basket_size"],
    )

    catalog.metrics["refund_rate"] = Metric(
        name="refund_rate",
        display_name="Refund Rate",
        description="Percentage of distinct orders that received a refund.",
        metric_type=MetricType.RATIO,
        sql_expression="COUNT(DISTINCT refunds.refund_id) * 1.0 / NULLIF(COUNT(DISTINCT orders.order_id), 0)",
        base_table="orders",
        grain=Grain.ORDER,
        unit="ratio",
        denominator_metric="order_count",
        synonyms=["refund_percentage", "return_rate"],
    )

    catalog.metrics["mrr"] = Metric(
        name="mrr",
        display_name="Monthly Recurring Revenue",
        description="Total active monthly recurring revenue from SaaS subscriptions.",
        metric_type=MetricType.SUM,
        sql_expression="SUM(subscriptions.mrr)",
        base_table="subscriptions",
        grain=Grain.SUBSCRIPTION,
        unit="USD",
        synonyms=["recurring_revenue", "subscription_revenue"],
    )

    catalog.metrics["churn_rate"] = Metric(
        name="churn_rate",
        display_name="Subscription Churn Rate",
        description="Proportion of subscriptions in churned status over total subscriptions.",
        metric_type=MetricType.RATIO,
        sql_expression="COUNT(DISTINCT CASE WHEN subscriptions.status = 'churned' THEN subscriptions.subscription_id END) * 1.0 / NULLIF(COUNT(DISTINCT subscriptions.subscription_id), 0)",
        base_table="subscriptions",
        grain=Grain.SUBSCRIPTION,
        unit="ratio",
        synonyms=["attrition_rate", "cancellation_rate"],
    )

    catalog.metrics["conversion_rate"] = Metric(
        name="conversion_rate",
        display_name="Checkout Conversion Rate",
        description="Proportion of sessions that resulted in a purchase conversion in A/B testing.",
        metric_type=MetricType.AVG,
        sql_expression="AVG(CASE WHEN ab_test_checkout.converted THEN 1.0 ELSE 0.0 END)",
        base_table="ab_test_checkout",
        grain=Grain.ORDER,
        unit="ratio",
        synonyms=["cvr", "checkout_cvr", "purchase_conversion"],
    )

    # 3. Dimensions
    catalog.dimensions["segment"] = Dimension(
        name="segment",
        entity_name="Customer",
        table_name="customers",
        column_name="segment",
        dim_type=DimensionType.CATEGORICAL,
        description="Customer account segment: Enterprise, Mid-Market, SMB, Consumer",
        grain=Grain.CUSTOMER,
        allowed_values=["Enterprise", "Mid-Market", "SMB", "Consumer"],
        synonyms=["customer_segment", "tier", "account_tier"],
    )

    catalog.dimensions["country"] = Dimension(
        name="country",
        entity_name="Customer",
        table_name="customers",
        column_name="country",
        dim_type=DimensionType.CATEGORICAL,
        description="Customer location country code",
        grain=Grain.CUSTOMER,
        synonyms=["geography", "geo", "market"],
    )

    catalog.dimensions["category"] = Dimension(
        name="category",
        entity_name="Product",
        table_name="products",
        column_name="category",
        dim_type=DimensionType.CATEGORICAL,
        description="Product product line",
        grain=Grain.PRODUCT,
        allowed_values=["Core Platform", "Pro Tools", "Enterprise Addon", "API Services"],
        synonyms=["product_category", "product_line"],
    )

    catalog.dimensions["channel_name"] = Dimension(
        name="channel_name",
        entity_name="MarketingChannel",
        table_name="marketing_channels",
        column_name="channel_name",
        dim_type=DimensionType.CATEGORICAL,
        description="Acquisition channel name",
        grain=Grain.CUSTOMER,
        synonyms=["channel", "acquisition_channel", "source"],
    )

    catalog.dimensions["quarter"] = Dimension(
        name="quarter",
        entity_name="Calendar",
        table_name="calendar_dim",
        column_name="quarter",
        dim_type=DimensionType.TEMPORAL,
        description="Calendar quarter (1, 2, 3, 4)",
        grain=Grain.QUARTER,
        synonyms=["qtr", "calendar_quarter"],
    )

    catalog.dimensions["fiscal_quarter"] = Dimension(
        name="fiscal_quarter",
        entity_name="Calendar",
        table_name="calendar_dim",
        column_name="fiscal_quarter",
        dim_type=DimensionType.TEMPORAL,
        description="Fiscal quarter string (e.g. Q2 2024, Q3 2024)",
        grain=Grain.QUARTER,
        synonyms=["quarter_str", "period"],
    )

    catalog.dimensions["month"] = Dimension(
        name="month",
        entity_name="Calendar",
        table_name="calendar_dim",
        column_name="month",
        dim_type=DimensionType.TEMPORAL,
        description="Calendar month integer (1 to 12)",
        grain=Grain.MONTH,
        synonyms=["calendar_month"],
    )

    catalog.dimensions["month_name"] = Dimension(
        name="month_name",
        entity_name="Calendar",
        table_name="calendar_dim",
        column_name="month_name",
        dim_type=DimensionType.TEMPORAL,
        description="Calendar month name (e.g. August, September)",
        grain=Grain.MONTH,
        synonyms=["month_str"],
    )

    catalog.dimensions["device"] = Dimension(
        name="device",
        entity_name="Order",
        table_name="orders",
        column_name="device",
        dim_type=DimensionType.CATEGORICAL,
        description="Device type: desktop, mobile, tablet",
        grain=Grain.ORDER,
        synonyms=["device_type", "client_device"],
    )

    catalog.dimensions["variant"] = Dimension(
        name="variant",
        entity_name="ABTestCheckout",
        table_name="ab_test_checkout",
        column_name="variant",
        dim_type=DimensionType.CATEGORICAL,
        description="Experiment variant (control_A, treatment_B)",
        grain=Grain.ORDER,
        synonyms=["ab_variant", "test_group", "experiment_arm"],
    )

    # 4. Allowable Relationships & Joins (strictly preventing cartesian fanouts)
    catalog.relationships = [
        Relationship(
            from_table="orders",
            to_table="customers",
            from_column="customer_id",
            to_column="customer_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN customers ON orders.customer_id = customers.customer_id",
            description="Orders placed by customer",
        ),
        Relationship(
            from_table="orders",
            to_table="calendar_dim",
            from_column="order_date_only",
            to_column="date_key",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN calendar_dim ON orders.order_date_only = calendar_dim.date_key",
            description="Orders calendar date",
        ),
        Relationship(
            from_table="orders",
            to_table="marketing_channels",
            from_column="channel_id",
            to_column="channel_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN marketing_channels ON orders.channel_id = marketing_channels.channel_id",
            description="Orders acquisition channel",
        ),
        Relationship(
            from_table="order_items",
            to_table="orders",
            from_column="order_id",
            to_column="order_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN orders ON order_items.order_id = orders.order_id",
            description="Order items header link",
        ),
        Relationship(
            from_table="order_items",
            to_table="products",
            from_column="product_id",
            to_column="product_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN products ON order_items.product_id = products.product_id",
            description="Order items product catalog link",
        ),
        Relationship(
            from_table="refunds",
            to_table="orders",
            from_column="order_id",
            to_column="order_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN orders ON refunds.order_id = orders.order_id",
            description="Refunds attached to orders",
        ),
        Relationship(
            from_table="payments",
            to_table="orders",
            from_column="order_id",
            to_column="order_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN orders ON payments.order_id = orders.order_id",
            description="Payments attached to orders",
        ),
        Relationship(
            from_table="subscriptions",
            to_table="customers",
            from_column="customer_id",
            to_column="customer_id",
            rel_type=RelationshipType.MANY_TO_ONE,
            join_clause="JOIN customers ON subscriptions.customer_id = customers.customer_id",
            description="Subscriptions attached to customer",
        ),
    ]

    return catalog
