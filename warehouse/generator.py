"""Synthetic Enterprise Data Warehouse Generator.

Generates realistic relational data across customers, products, marketing channels,
orders, order_items, subscriptions, payments, refunds, and calendar dimensions,
with seeded business scenarios (revenue decline, Simpson's paradox, refund surge).
"""

from __future__ import annotations

import datetime
from typing import Dict, Any, Tuple
import duckdb
import numpy as np
import pandas as pd


class WarehouseGenerator:
    """Generates synthetic enterprise data warehouse tables and seeds scenarios."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_all(self, start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> Dict[str, pd.DataFrame]:
        """Generate all relational warehouse tables with embedded scenarios."""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # 1. Calendar Dimension
        calendar_df = self._generate_calendar(start, end)
        
        # 2. Customers
        n_customers = 2500
        customers_df = self._generate_customers(n_customers, start)
        
        # 3. Products
        products_df = self._generate_products()
        
        # 4. Marketing Channels
        channels_df = self._generate_channels()
        
        # 5. Orders & Order Items (incorporating Q3 revenue decline & checkout experiment)
        orders_df, order_items_df = self._generate_orders_and_items(
            customers_df, products_df, channels_df, calendar_df, start, end
        )
        
        # 6. Subscriptions
        subscriptions_df = self._generate_subscriptions(customers_df, start, end)
        
        # 7. Payments & Refunds (incorporating August Pro Tools refund spike)
        payments_df, refunds_df = self._generate_payments_and_refunds(orders_df)
        
        # 8. Experiment / A/B Test Logs (Simpson's Paradox in Checkout Redesign)
        ab_test_df = self._generate_checkout_experiment(customers_df)

        return {
            "calendar_dim": calendar_df,
            "customers": customers_df,
            "products": products_df,
            "marketing_channels": channels_df,
            "orders": orders_df,
            "order_items": order_items_df,
            "subscriptions": subscriptions_df,
            "payments": payments_df,
            "refunds": refunds_df,
            "ab_test_checkout": ab_test_df,
        }

    def _generate_calendar(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
        dates = pd.date_range(start, end, freq="D")
        records = []
        for d in dates:
            records.append({
                "date_key": d.strftime("%Y-%m-%d"),
                "year": int(d.year),
                "quarter": int(d.quarter),
                "month": int(d.month),
                "month_name": d.strftime("%B"),
                "day": int(d.day),
                "day_of_week": int(d.dayofweek),
                "is_weekend": bool(d.dayofweek >= 5),
                "fiscal_quarter": f"Q{d.quarter} {d.year}",
            })
        return pd.DataFrame(records)

    def _generate_customers(self, n: int, start: pd.Timestamp) -> pd.DataFrame:
        segments = ["Enterprise", "Mid-Market", "SMB", "Consumer"]
        segment_weights = [0.08, 0.22, 0.40, 0.30]
        countries = ["US", "UK", "DE", "FR", "CA", "AU", "JP"]
        country_weights = [0.45, 0.15, 0.12, 0.08, 0.08, 0.06, 0.06]
        industries = ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", "Education"]

        records = []
        for i in range(1, n + 1):
            created_offset = int(self.rng.integers(0, 180))
            created_at = start - pd.Timedelta(days=created_offset)
            records.append({
                "customer_id": i,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "segment": self.rng.choice(segments, p=segment_weights),
                "country": self.rng.choice(countries, p=country_weights),
                "industry": self.rng.choice(industries),
                "credit_score": int(self.rng.normal(700, 50)),
                "is_active": True,
            })
        return pd.DataFrame(records)

    def _generate_products(self) -> pd.DataFrame:
        items = [
            (101, "Core Cloud Starter", "Core Platform", 99.0, 30.0),
            (102, "Core Cloud Growth", "Core Platform", 299.0, 75.0),
            (103, "Enterprise Suite v1", "Core Platform", 1299.0, 250.0),
            (201, "Pro Analytics Addon", "Pro Tools", 149.0, 35.0),
            (202, "Pro Pipeline Accelerator", "Pro Tools", 249.0, 55.0),
            (301, "Dedicated Account Architect", "Enterprise Addon", 999.0, 300.0),
            (302, "Custom SLA Guarantee", "Enterprise Addon", 1499.0, 400.0),
            (401, "API Ingestion Gateway", "API Services", 199.0, 40.0),
            (402, "Realtime Streaming API", "API Services", 499.0, 90.0),
        ]
        records = [
            {"product_id": pid, "name": name, "category": cat, "base_price": price, "cost": cost}
            for pid, name, cat, price, cost in items
        ]
        return pd.DataFrame(records)

    def _generate_channels(self) -> pd.DataFrame:
        channels = [
            (1, "Organic Search", "Low"),
            (2, "Paid Search", "High"),
            (3, "Social Media", "Medium"),
            (4, "Email Nurture", "Low"),
            (5, "Partner Referral", "Medium"),
            (6, "Outbound Enterprise", "High"),
        ]
        records = [
            {"channel_id": cid, "channel_name": name, "acquisition_cost_tier": tier}
            for cid, name, tier in channels
        ]
        return pd.DataFrame(records)

    def _generate_orders_and_items(
        self,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        channels_df: pd.DataFrame,
        calendar_df: pd.DataFrame,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate orders and order items with injected Q3 revenue decline."""
        cust_lookup = customers_df.set_index("customer_id").to_dict(orient="index")
        prod_lookup = products_df.set_index("product_id").to_dict(orient="index")
        prod_ids = products_df["product_id"].tolist()
        channel_ids = channels_df["channel_id"].tolist()
        devices = ["desktop", "mobile", "tablet"]
        device_weights = [0.55, 0.35, 0.10]

        total_days = (end - start).days + 1
        orders = []
        order_items = []
        order_counter = 10001
        item_counter = 50001

        # We simulate baseline ~40-60 orders per day.
        # Scenario injection: In Q3 2024 (2024-07-01 to 2024-09-30),
        # Enterprise pricing changes caused an immediate dip in enterprise transactions
        # and total revenue drops by ~8.2% relative to Q2.
        for day_offset in range(total_days):
            current_date = start + pd.Timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            quarter = current_date.quarter
            is_q3 = (quarter == 3)
            is_q2 = (quarter == 2)

            # Base number of orders
            daily_order_count = int(self.rng.integers(45, 65))
            if is_q3:
                # Slight seasonal softening (-2%)
                daily_order_count = int(daily_order_count * 0.98)

            for _ in range(daily_order_count):
                cust_id = int(self.rng.choice(customers_df["customer_id"]))
                cust_info = cust_lookup[cust_id]
                segment = cust_info["segment"]

                # In Q3, Enterprise buyers curtailed purchases due to price hike
                if is_q3 and segment == "Enterprise" and self.rng.random() < 0.13:
                    continue

                order_dt = current_date + pd.Timedelta(
                    hours=int(self.rng.integers(8, 22)),
                    minutes=int(self.rng.integers(0, 59)),
                    seconds=int(self.rng.integers(0, 59)),
                )

                # Channel assignment: Enterprise favors Outbound (channel 6)
                if segment == "Enterprise":
                    ch_id = 6 if self.rng.random() < 0.60 else int(self.rng.choice(channel_ids))
                else:
                    ch_id = int(self.rng.choice(channel_ids))

                device = self.rng.choice(devices, p=device_weights)

                # Items in order
                if segment == "Enterprise":
                    num_items = int(self.rng.integers(2, 5))
                    chosen_prods = self.rng.choice([103, 301, 302, 402], size=num_items)
                elif segment == "Mid-Market":
                    num_items = int(self.rng.integers(1, 3))
                    chosen_prods = self.rng.choice([102, 201, 202, 401], size=num_items)
                else:
                    num_items = 1
                    chosen_prods = self.rng.choice([101, 201, 401], size=1)

                order_gross = 0.0
                for pid in chosen_prods:
                    p_info = prod_lookup[pid]
                    qty = 1 if segment in ["Consumer", "SMB"] else int(self.rng.integers(1, 4))
                    unit_price = float(p_info["base_price"])

                    # On July 1st, Enterprise addon prices were bumped 20%, but volume plummeted
                    if is_q3 and pid in [103, 301, 302]:
                        unit_price *= 1.20

                    net_amt = round(qty * unit_price, 2)
                    order_gross += net_amt

                    order_items.append({
                        "item_id": item_counter,
                        "order_id": order_counter,
                        "product_id": int(pid),
                        "quantity": qty,
                        "unit_price": unit_price,
                        "net_amount": net_amt,
                    })
                    item_counter += 1

                discount = round(order_gross * 0.05, 2) if self.rng.random() < 0.2 else 0.0
                shipping = 0.0
                total_amt = round(order_gross - discount, 2)

                orders.append({
                    "order_id": order_counter,
                    "customer_id": cust_id,
                    "channel_id": ch_id,
                    "order_date": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "order_date_only": date_str,
                    "status": "completed",
                    "device": device,
                    "discount_amount": discount,
                    "shipping_amount": shipping,
                    "total_amount": total_amt,
                })
                order_counter += 1

        return pd.DataFrame(orders), pd.DataFrame(order_items)

    def _generate_subscriptions(
        self, customers_df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
    ) -> pd.DataFrame:
        """Generate subscription histories with higher Q3 Enterprise churn."""
        records = []
        sub_id = 1
        for _, cust in customers_df.iterrows():
            cid = cust["customer_id"]
            segment = cust["segment"]
            tier = "Enterprise" if segment == "Enterprise" else ("Pro" if segment == "Mid-Market" else "Basic")
            price_map = {"Enterprise": 1200.0, "Pro": 299.0, "Basic": 49.0}
            mrr = price_map[tier]

            sub_start = pd.to_datetime(cust["created_at"]).date()
            status = "active"
            end_date = None

            # Q3 Enterprise churn spike
            if segment == "Enterprise" and self.rng.random() < 0.18:
                churn_day = self.rng.integers(1, 90)
                churn_dt = pd.to_datetime("2024-07-01") + pd.Timedelta(days=churn_day)
                if churn_dt <= end:
                    status = "churned"
                    end_date = churn_dt.strftime("%Y-%m-%d")
            elif self.rng.random() < 0.06:
                churn_day = self.rng.integers(30, 200)
                churn_dt = start + pd.Timedelta(days=churn_day)
                if churn_dt <= end:
                    status = "churned"
                    end_date = churn_dt.strftime("%Y-%m-%d")

            records.append({
                "subscription_id": sub_id,
                "customer_id": cid,
                "plan_tier": tier,
                "status": status,
                "start_date": str(sub_start),
                "end_date": end_date,
                "monthly_price": mrr,
                "mrr": mrr if status == "active" else 0.0,
            })
            sub_id += 1
        return pd.DataFrame(records)

    def _generate_payments_and_refunds(self, orders_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate payments and refunds with August Pro Tools defect refund surge."""
        payments = []
        refunds = []
        pay_id = 1
        ref_id = 1

        for _, order in orders_df.iterrows():
            oid = order["order_id"]
            odt = pd.to_datetime(order["order_date"])
            amt = order["total_amount"]
            pdate = odt + pd.Timedelta(minutes=int(self.rng.integers(1, 15)))

            payments.append({
                "payment_id": pay_id,
                "order_id": oid,
                "payment_date": pdate.strftime("%Y-%m-%d %H:%M:%S"),
                "payment_method": self.rng.choice(["credit_card", "bank_transfer", "paypal"], p=[0.7, 0.2, 0.1]),
                "amount": amt,
                "status": "successful",
            })
            pay_id += 1

            # Normal refund rate is 2%
            # In August 2024 (2024-08-01 to 2024-08-31), defective update causes refund surge to 14%
            is_august = (odt.year == 2024 and odt.month == 8)
            refund_prob = 0.14 if is_august else 0.02

            if self.rng.random() < refund_prob:
                ref_dt = odt + pd.Timedelta(days=int(self.rng.integers(1, 5)))
                reason = "defective_update" if is_august else self.rng.choice(["dissatisfied", "pricing_dispute", "duplicate"])
                refunds.append({
                    "refund_id": ref_id,
                    "order_id": oid,
                    "refund_date": ref_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "amount": amt,
                    "reason": reason,
                })
                ref_id += 1

        return pd.DataFrame(payments), pd.DataFrame(refunds)

    def _generate_checkout_experiment(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        """Simulate A/B experiment designed to test Simpson's Paradox.

        Variant A (Control / Original Checkout):
          - Desktop conversion: 50%
          - Mobile conversion: 20%
          - Traffic: 20% Desktop, 80% Mobile
          - Aggregate conversion: 0.20*0.50 + 0.80*0.20 = 26.0%

        Variant B (Treatment / Redesigned Checkout):
          - Desktop conversion: 42% (lower than A!)
          - Mobile conversion: 15% (lower than A!)
          - Traffic: 80% Desktop, 20% Mobile (heavily biased towards desktop)
          - Aggregate conversion: 0.80*0.42 + 0.20*0.15 = 36.6% (APPEARS HIGHER!)
        """
        records = []
        n_sessions = 6000
        for i in range(1, n_sessions + 1):
            # Assign variant: 50/50 split overall
            variant = "treatment_B" if self.rng.random() < 0.50 else "control_A"

            if variant == "control_A":
                device = "desktop" if self.rng.random() < 0.20 else "mobile"
                p_conv = 0.50 if device == "desktop" else 0.20
            else:
                device = "desktop" if self.rng.random() < 0.80 else "mobile"
                p_conv = 0.42 if device == "desktop" else 0.15

            converted = bool(self.rng.random() < p_conv)
            records.append({
                "session_id": i,
                "variant": variant,
                "device": device,
                "converted": converted,
                "session_date": "2024-09-15",
            })
        return pd.DataFrame(records)


def create_in_memory_warehouse(seed: int = 42) -> duckdb.DuckDBPyConnection:
    """Create and populate an in-memory DuckDB warehouse with all tables."""
    gen = WarehouseGenerator(seed=seed)
    dfs = gen.generate_all()
    con = duckdb.connect(database=":memory:")
    for table_name, df in dfs.items():
        con.register(f"temp_{table_name}", df)
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_{table_name}")
        con.unregister(f"temp_{table_name}")
    return con


def save_warehouse_to_duckdb(file_path: str, seed: int = 42) -> None:
    """Persist generated warehouse to a DuckDB database file."""
    gen = WarehouseGenerator(seed=seed)
    dfs = gen.generate_all()
    con = duckdb.connect(database=file_path)
    for table_name, df in dfs.items():
        con.register(f"temp_{table_name}", df)
        con.execute(f"DROP TABLE IF EXISTS {table_name}")
        con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_{table_name}")
        con.unregister(f"temp_{table_name}")
    con.close()
