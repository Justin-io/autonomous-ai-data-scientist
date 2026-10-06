"""Semantic Layer Data Models.

Defines Pydantic models for Entities, Metrics, Dimensions, Relationships,
Column Metadata, Grains, and Semantic Catalogs.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Grain(str, Enum):
    CUSTOMER = "customer"
    ORDER = "order"
    ORDER_ITEM = "order_item"
    PRODUCT = "product"
    SUBSCRIPTION = "subscription"
    PAYMENT = "payment"
    REFUND = "refund"
    DAY = "day"
    MONTH = "month"
    QUARTER = "quarter"


class MetricType(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    RATIO = "RATIO"
    DERIVED = "DERIVED"


class DimensionType(str, Enum):
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    BOOLEAN = "boolean"
    NUMERIC = "numeric"


class RelationshipType(str, Enum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:N"


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    description: str = ""
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references_table: Optional[str] = None
    references_column: Optional[str] = None
    pii: bool = False
    synonyms: List[str] = Field(default_factory=list)


class Entity(BaseModel):
    name: str
    table_name: str
    primary_key: str
    description: str
    grain: Grain
    freshness: str = "daily"
    columns: Dict[str, ColumnMetadata] = Field(default_factory=dict)
    caveats: List[str] = Field(default_factory=list)


class Dimension(BaseModel):
    name: str
    entity_name: str
    table_name: str
    column_name: str
    dim_type: DimensionType
    description: str
    grain: Grain
    allowed_values: Optional[List[str]] = None
    synonyms: List[str] = Field(default_factory=list)


class Metric(BaseModel):
    name: str
    display_name: str
    description: str
    metric_type: MetricType
    sql_expression: str
    base_table: str
    grain: Grain
    unit: str = "USD"
    denominator_metric: Optional[str] = None
    required_joins: List[str] = Field(default_factory=list)
    business_rules: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    from_table: str
    to_table: str
    from_column: str
    to_column: str
    rel_type: RelationshipType
    allowed: bool = True
    join_clause: str
    description: str = ""
