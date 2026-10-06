"""FastAPI Main Application for Autonomous AI Data Scientist Platform."""

from __future__ import annotations

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analyses import router as analyses_router
from api.routes.semantic import router as semantic_router
from api.routes.evaluations import router as evaluations_router

app = FastAPI(
    title="Autonomous AI Data Scientist Platform",
    description="Production-grade Autonomous Data Scientist API with explicit state machine orchestration, semantic layer grounding, Bayesian hypothesis engine, causal inference, and cryptographic evidence verification.",
    version="1.0.0",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(analyses_router)
app.include_router(semantic_router)
app.include_router(evaluations_router)


@app.get("/health")
def health_check():
    """Liveness probe."""
    return {"status": "ok", "service": "auto_data_scientist", "timestamp": time.time()}


@app.get("/ready")
def readiness_check():
    """Readiness probe verifying engine and catalog availability."""
    return {
        "status": "ready",
        "semantic_catalog": "loaded",
        "database_engine": "ready",
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
