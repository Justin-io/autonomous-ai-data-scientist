# Implementation Plan
## Autonomous AI Data Scientist Platform

This plan follows the Ralph-style iterative autonomous development loop:
1. Inspect repo, architecture, PRD, task registry, and test results.
2. Pick the single highest-value incomplete capability.
3. Understand dependencies and integration points.
4. Define acceptance criteria.
5. Implement the smallest complete vertical increment.
6. Write/run tests (unit, integration, regression).
7. Diagnose root causes of any failure and fix.
8. Perform independent self-critique.
9. Update persistent task registry and progress logs.
10. Commit verified increment to git.

---

### Phase 1: Foundation & Data Warehouse (Vertical Slice 0)
- **Goal**: Realistic synthetic data warehouse and seed data with reproducible business anomalies, DuckDB engine, and semantic layer models.
- **Components**:
  - `warehouse/generator.py`: Generates customers, products, orders, order items, subscriptions, refunds, marketing channels, calendar.
  - `warehouse/scenarios.py`: Seeds reproducible business scenarios (e.g. Q3 revenue drop 8% from price increase and enterprise churn; Simpson's paradox in marketing conversion; refund spike).
  - `core/semantic_layer/`: Pydantic models for Entity, Metric, Dimension, Relationship, and JoinGraph.
  - `core/db/`: Database connector supporting DuckDB and PostgreSQL with read-only enforcement.
- **Verification**: Tests checking table counts, integrity constraints, scenario metrics, and semantic layer lookups.

---

### Phase 2: SQL Engine, AST Validation & Cost Estimator (Vertical Slice 1)
- **Goal**: SQL generator, AST parser, read-only verifier, join fanout detector, and cost estimator.
- **Components**:
  - `core/sql_engine/validator.py`: `sqlglot` based AST parser, read-only guarantee, schema check, fanout guard.
  - `core/sql_engine/optimizer.py`: EXPLAIN plan cost estimation, query hashing, predicate optimization.
  - `core/sql_engine/generator.py`: Grounded SQL generation from semantic metrics and filters.
- **Verification**: Tests with malicious SQL injection attempts, mutating queries, fanout queries, and valid semantic queries.

---

### Phase 3: State Machine Orchestrator & Autonomous Loop (Vertical Slice 2)
- **Goal**: Explicit state machine managing all 21 states with bounded loop controls and event recording.
- **Components**:
  - `core/orchestrator/state_machine.py`: Deterministic state machine with transition guards and states.
  - `core/orchestrator/context.py`: Durable analysis context, event log, token/cost budgets.
  - `core/orchestrator/agent.py`: OBSERVE -> PLAN -> ACT -> CRITIQUE -> RECORD loop.
- **Verification**: State transition tests, loop termination tests, budget exhaustion tests.

---

### Phase 4: Hypothesis Engine & Statistical / Anomaly Tooling (Vertical Slice 3)
- **Goal**: Competing hypothesis generation, ranking, Bayesian probability updates, statistical tests, and anomaly detection.
- **Components**:
  - `core/hypothesis/engine.py`: Multi-hypothesis generator, ranking by information gain, Bayesian posterior updates.
  - `core/statistics/inferential.py`: Two-sample t-test, Mann-Whitney, Chi-square, ANOVA, 95% CIs, Cohen's d.
  - `core/statistics/anomalies.py`: IQR, Hampel filter, Rolling Z-score, Isolation Forest.
  - `core/statistics/segmentation.py`: Shift-share contribution analysis across dimensions.
- **Verification**: Statistical tests against synthetic ground truth, known anomaly detection accuracy.

---

### Phase 5: Causal Analysis, Independent Critic & Evidence Verifier (Vertical Slice 4)
- **Goal**: Causal vs associative inference, assumption checks, Critic Agent auditing for biases, and calibrated confidence scoring.
- **Components**:
  - `core/causal/engine.py`: Difference-in-Differences, propensity weighting, assumption checks, defensive associative downgrading.
  - `core/critic/agent.py`: Simpson's paradox detector, multiple testing correction (Bonferroni, FDR), p-hacking audit.
  - `core/evidence/store.py`: Immutable evidence store with SHA-256 data hashes.
  - `core/evidence/confidence.py`: Calibrated multi-factor confidence calculator.
  - `core/evidence/verifier.py`: Deterministic numeric claim verifier against evidence hashes.
- **Verification**: Trap detection tests (Simpson's paradox, causal overclaiming, hallucinated number rejection).

---

### Phase 6: Plotly Visualizer, Report Generator & HITL (Vertical Slice 5)
- **Goal**: Structured evidence-backed analyst reports with Plotly visualizations and HITL approval checkpoints.
- **Components**:
  - `core/visuals/generator.py`: Analytical intent-based Plotly chart generation.
  - `core/report/generator.py`: Structured analyst report synthesis with cryptographic citation markers.
  - `core/hitl/manager.py`: Human-in-the-loop pause, review packet generation, and resume handlers.
- **Verification**: Report structure validation, citation integrity check, HITL trigger tests.

---

### Phase 7: FastAPI Backend & Evaluation Harness (Vertical Slice 6)
- **Goal**: Production REST API with SSE events, background tasks, and benchmark evaluation harness.
- **Components**:
  - `api/main.py`, `api/routes/`: FastAPI endpoints (`/analyses`, `/events`, `/evidence`, `/approve`, `/evaluations`).
  - `eval/benchmark_suite.py`: Benchmark business questions with ground truth.
  - `eval/harness.py`: Automated evaluation measuring accuracy, citation completeness, latency, cost.
- **Verification**: API tests via TestClient / httpx, end-to-end benchmark execution.

---

### Phase 8: React + TypeScript Analyst Workspace Frontend (Vertical Slice 7)
- **Goal**: Interactive web workspace for analysts.
- **Components**:
  - `frontend/`: React + TypeScript + Vite app with real-time SSE trajectory, SQL viewer, hypothesis tree, Plotly charts, citation popovers, and HITL approval modal.
- **Verification**: Frontend build, type checks, and end-to-end integration with FastAPI backend.

---

### Phase 9: Packaging, Docker & AWS Production Deployment (Vertical Slice 8)
- **Goal**: Containerization, CI config, and AWS deployment documentation.
- **Components**:
  - `Dockerfile`, `docker-compose.yml`, `docs/AWS_DEPLOYMENT.md`, `Makefile`.
- **Verification**: Docker compose build verification, full test suite execution.
