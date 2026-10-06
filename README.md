# Autonomous AI Data Scientist Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.0+-FFF000.svg?logo=duckdb)](https://duckdb.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg?logo=typescript)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/tests-46%20passed-brightgreen.svg)]()

> A production-grade, closed-loop Autonomous AI Data Scientist platform that autonomously investigates complex business questions, enforces canonical semantic grounding, tests competing Bayesian hypotheses, performs rigorous inferential and causal analysis, audits findings with an independent Critic Agent, and generates cryptographically verified executive reports with an interactive React + TypeScript analyst workspace.

---

## 🎯 Key Capabilities

- **21-State Machine Orchestration**: Deterministic closed-loop state machine (`OBSERVE -> INTERPRET -> PLAN -> ACT -> VERIFY -> CRITIQUE -> CORRECT -> REVERIFY -> RECORD -> CONTINUE`) with machine-checkable guards, retry budgets, and execution bounds.
- **Canonical Semantic Layer**: Grounded catalog of entities, metrics, dimensions, grain definitions, and allowable join paths to prevent join fanout and schema hallucination.
- **SQL AST Validation & Cost Estimator**: Powered by `sqlglot`, strictly rejects mutating statements (`DROP`, `DELETE`, `UPDATE`, `INSERT`), resolves table aliases, enforces read-only access, checks PII policies, and generates EXPLAIN plan cost estimates.
- **Bayesian Competing Hypothesis Engine**: Synthesizes multiple falsifiable hypotheses, ranks them by expected information gain, updates posterior probabilities on empirical evidence, and logs explicit reasons for refutations.
- **Rigorous Inferential & Effect-Size Statistics**: Welch's t-test, Mann-Whitney U, Chi-square, Cohen's d, Relative Risk, and 95% Confidence Intervals.
- **Anomaly Detection & Multi-Dimensional Segmentation**: Hampel filter, IQR fences, Isolation Forest, changepoint analysis, and multi-dimensional shift-share contribution analysis.
- **Causal Inference with Defensive Downgrading**: Difference-in-Differences (DiD) estimator with unconfoundedness checks; automatically downgrades observational findings to `ASSOCIATIVE` with explicit confounding warnings when identification assumptions are not satisfied.
- **Independent Critic Agent**: Audits analysis trajectories for Simpson's paradox, denominator traps, p-hacking, and applies Benjamini-Hochberg False Discovery Rate (FDR) corrections.
- **Cryptographic Evidence Store & Calibrated Confidence**: Every factual claim is bound to an immutable SHA-256 dataset hash (`[EVD-...]`), scored across 4 calibrated confidence dimensions (0.0–1.0), and validated with a deterministic claim verifier.
- **Human-in-the-Loop (HITL) Checkpoint**: Pauses execution when confidence drops below 0.70 or high-risk claims arise, presenting a structured review packet for human approval or adjustment.
- **Interactive React + TypeScript Workspace**: 21-state visual progress stepper, real-time SSE streaming telemetry, benchmark presets (BQ-1, BQ-2, BQ-3), interactive Plotly charts, 7 inspector tabs, and benchmark scorecard.

---

## 🏗️ Architecture

```
                               +-----------------------------+
                               |     React + TypeScript      |
                               |      Analyst Workspace      |
                               +--------------+--------------+
                                              | HTTP / SSE
                                              v
                               +-----------------------------+
                               |       FastAPI Backend       |
                               |    (Routers, Schemas, SSE)  |
                               +--------------+--------------+
                                              |
                    +-------------------------+-------------------------+
                    |                                                   |
                    v                                                   v
+--------------------------------------+             +---------------------------------------+
|  Autonomous Orchestrator State Mch   |             |             Semantic Layer            |
|  (OBSERVE -> PLAN -> ACT -> CRITIQUE)|<----------->|  Entities, Metrics, Dimensions, Joins |
+------------------+-------------------+             +---------------------------------------+
                   |
     +-------------+-------------+-------------+-------------+
     |             |             |             |             |
     v             v             v             v             v
+----------+ +-----------+ +-----------+ +-----------+ +-----------+
|   SQL    | |Hypothesis | |Statistical| |  Causal   | |  Critic   |
| Engine & | |  Engine   | |& Anomaly  | | Inference | |   Agent   |
|Validator | | (Bayes)   | |  Engine   | |  Engine   | |(Audit/Trap|
+----+-----+ +-----+-----+ +-----+-----+ +-----+-----+ +-----+-----+
     |             |             |             |             |
     +-------------+-------------+-------------+-------------+
                                 |
                                 v
                 +-------------------------------+
                 |  Evidence Store & Verifier    |
                 |  (Data Hashes, Calibrated Conf|
                 +---------------+---------------+
                                 |
                   +-------------+-------------+
                   |                           |
                   v                           v
     +--------------------------+   +--------------------------+
     |   PostgreSQL Data Hub    |   |     DuckDB Analytics     |
     |  (Read-Only Analytical)  |   |  (Fast Columnar Engine)  |
     +--------------------------+   +--------------------------+
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for building the frontend)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/<your-username>/autonomous-ai-data-scientist.git
cd autonomous-ai-data-scientist

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# (Optional) Build frontend
cd frontend
npm install
npm run build
cd ..
```

### 3. Generate Warehouse & Run Tests
```bash
# Seed synthetic analytics warehouse (10 tables with reproducible scenarios)
python -m warehouse.generator

# Run the full test suite (46 tests across 10 suites)
pytest tests/ -v
```

### 4. Start the Application
```bash
# Start FastAPI backend (serves API and compiled React SPA on port 8000)
uvicorn api.main:app --host 0.0.0.0 --port 8000
```
Open your browser at **`http://localhost:8000`**.

---

## 🐳 Docker & Docker Compose

Run the entire platform with PostgreSQL and the application containerized:

```bash
docker-compose up --build
```

Access the UI at `http://localhost:8000` and API docs at `http://localhost:8000/docs`.

---

## 📊 Benchmark Evaluation Suite

The platform includes canonical business benchmark questions:

| ID | Business Question | Ground Truth Mechanism |
|---|---|---|
| **BQ-1** | *"Why did our net revenue decline ~8% in Q3 2024?"* | Enterprise tier contraction (-15.5%) post-pricing change explains 109.8% of variance. |
| **BQ-2** | *"Did the checkout redesign improve conversion rate?"* | Simpson's Paradox: overall conversion increased (+0.5%), but mobile dropped (-1.6%) and desktop dropped (-1.2%) due to traffic mix shift. |
| **BQ-3** | *"What drove the surge in customer refunds in August 2024?"* | Integration webhook bug caused duplicate billing on Subscription Pro plans, spiking refunds 4.8x. |

Run benchmark evaluations programmatically:
```bash
python -m eval.harness
```

---

## ☁️ Production Deployment

See [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) for full enterprise AWS deployment architecture:
- **Compute**: Amazon ECS Fargate with Application Load Balancer
- **Data Hub**: Amazon RDS PostgreSQL (Multi-AZ) & Amazon S3 Parquet Lake
- **Monitoring**: AWS CloudWatch metrics, alarms, and OpenTelemetry distributed tracing
- **Infrastructure as Code**: Terraform configuration templates

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
