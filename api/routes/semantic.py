"""Semantic catalog router providing discovery of entities, metrics, and dimensions."""

from __future__ import annotations

from fastapi import APIRouter
from core.semantic_layer.catalog import build_default_semantic_catalog

router = APIRouter(prefix="/api/v1/semantic", tags=["semantic"])
_CATALOG = build_default_semantic_catalog()


@router.get("/catalog")
def get_semantic_catalog():
    """Retrieve all canonical entities, metrics, dimensions, and allowable relationships."""
    return {
        "entities": {k: v.model_dump() for k, v in _CATALOG.entities.items()},
        "metrics": {k: v.model_dump() for k, v in _CATALOG.metrics.items()},
        "dimensions": {k: v.model_dump() for k, v in _CATALOG.dimensions.items()},
        "relationships": [r.model_dump() for r in _CATALOG.relationships],
    }


@router.get("/metrics")
def list_metrics():
    """List available canonical business metrics."""
    return [
        {
            "name": m.name,
            "display_name": m.display_name,
            "description": m.description,
            "unit": m.unit,
            "grain": m.grain.value,
            "sql_expression": m.sql_expression,
        }
        for m in _CATALOG.metrics.values()
    ]


@router.get("/dimensions")
def list_dimensions():
    """List available canonical dimensions."""
    return [
        {
            "name": d.name,
            "table_name": d.table_name,
            "dim_type": d.dim_type.value,
            "description": d.description,
            "allowed_values": d.allowed_values,
        }
        for d in _CATALOG.dimensions.values()
    ]
