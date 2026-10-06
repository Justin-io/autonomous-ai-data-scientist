# System Architecture Document
## Autonomous AI Data Scientist Platform

### 1. High-Level Architecture Overview

```
                               +-----------------------------+
                               |     React + TypeScript      |
                               |      Analyst Workspace      |
                               +--------------+--------------+
                                              | HTTP / SSE / WS
                                              v
                               +-----------------------------+
                               |       FastAPI Backend       |
                               |    (Routers, Schemas, OTel) |
                               +--------------+--------------+
                                              |
                   +--------------------------+--------------------------+
                   |                                                     |
                   v                                                     v
+--------------------------------------+             +---------------------------------------+
|  Autonomous Orchestrator State Mch  |             |             Semantic Layer            |
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

### 2. Explicit State Machine Definition

The analysis trajectory is managed by an explicit, deterministically monitored state machine with the following states:

1. `QUESTION_RECEIVED`: Ingestion and validation of natural language input.
2. `INTENT_PARSED`: Extraction of target metric, entity, temporal scope, comparison periods, and analytical goal.
3. `SEMANTIC_GROUNDED`: Matching parsed intent to canonical semantic models, metrics, grain, and allowable dimensions.
4. `PLAN_CREATED`: Multi-step investigation DAG formulation with falsifiable hypotheses and required evidence.
5. `SQL_DRAFTED`: SQL dialect generation for PostgreSQL / DuckDB.
6. `SQL_VALIDATED`: AST parsing via `sqlglot`, read-only check, schema verification, join cardinality check, fanout prevention.
7. `QUERY_COST_ESTIMATED`: EXPLAIN cost evaluation, partition check, execution approval.
8. `QUERY_EXECUTED`: Execution against DuckDB / PostgreSQL with strict row limits and timeouts.
9. `DATA_PROFILED`: Schema validation, summary statistics, missingness, zero rates, cardinality profiling.
10. `HYPOTHESES_GENERATED`: Competing hypotheses synthesized based on preliminary data profile.
11. `HYPOTHESES_RANKED`: Prioritization via expected information gain and verification cost.
12. `HYPOTHESIS_TESTED`: Execution of targeted statistical sub-queries and hypothesis evaluation.
13. `SEGMENTS_ANALYZED`: Multi-dimensional segment contribution decomposition across dimensions.
14. `ANOMALIES_DETECTED`: Time-series and distributional anomaly detection (IQR, Hampel, Isolation Forest).
15. `CAUSALITY_ASSESSED`: Rigorous causal inference assumption checking (DiD, propensity matching) or associative downgrade.
16. `VISUALS_CREATED`: Plotly JSON specification generation suited to analytical intent.
17. `CRITIQUE_COMPLETED`: Independent Critic Agent auditing for biases, Simpson's paradox, p-hacking, and causal overreach.
18. `EVIDENCE_VERIFIED`: Deterministic verification linking all quantitative statements to hashed evidence records.
19. `REPORT_DRAFTED`: Synthesizing structured markdown report with citations, confidence scores, and limitations.
20. `HUMAN_REVIEW_REQUIRED`: Pauses state machine for human operator sign-off if risk/uncertainty thresholds tripped.
21. `COMPLETE`: Final artifact generation, audit trail saved, and task finalized.
22. `FAILED`: Terminal error state with actionable diagnostics and root-cause logging.

---

### 3. Component Architecture

#### 3.1 Semantic Layer (`core/semantic_layer`)
- **Entities**: Business objects (`Customer`, `Product`, `Subscription`, `Order`).
- **Metrics**: Canonical metrics with aggregation formulas (`revenue = SUM(order_items.net_amount)`, `churn_rate`, `aov`, `refund_rate`).
- **Dimensions**: Slicing attributes with grain specifications (`customer.segment`, `product.category`, `calendar.quarter`).
- **Relationships & Joins**: Strict graph of allowable joins with cardinalities (`1:N`, `N:1`, `1:1`) to prevent cartesian explosion and fanout duplication.
- **Synonyms & Context**: Natural-language mapping, business caveats, freshness rules.

#### 3.2 SQL Generator, Validator & Optimizer (`core/sql_engine`)
- **AST Parser (`sqlglot`)**: Validates syntax, forbids mutations (`INSERT`, `UPDATE`, `DROP`, `ALTER`, `GRANT`, `COPY`), enforces `SELECT` only.
- **Schema & Grain Validator**: Cross-checks tables and columns against database catalog; checks `GROUP BY` matches aggregation grain.
- **Fanout & Cardinality Guard**: Ensures join paths don't multiply rows across one-to-many joins without appropriate grouping.
- **Optimizer**: Query cost estimation via `EXPLAIN`, predicate pushdown, and query caching.
- **Dual Execution Engine**: Executes against DuckDB (in-memory columnar analytical store) and PostgreSQL analytical replica.

#### 3.3 Autonomous Hypothesis Engine (`core/hypothesis`)
- Formulates multiple mutually exclusive and collectively exhaustive (MECE) hypotheses.
- Tracks prior probability, likelihood, posterior probability, and status (`PENDING`, `CONFIRMED`, `REFUTED`, `INCONCLUSIVE`).
- Computes Information Gain to select the next optimal analytical query.
- Explicitly logs falsification reasons for rejected hypotheses.

#### 3.4 Statistical & Anomaly Engine (`core/statistics`)
- **Descriptive Statistics**: Central tendency, dispersion, percentiles, skewness.
- **Inferential Tests**: Two-sample t-test, Mann-Whitney U test, Chi-square test of independence, One-way ANOVA.
- **Effect Sizes**: Cohen's d, Relative Risk, Odds Ratio.
- **Anomaly Detection**: Rolling Z-score, Hampel filter / IQR, Isolation Forest, Change-point detection.
- **Contribution Analysis**: Multi-dimensional shift-share decomposition calculating segment contribution to top-line variance.

#### 3.5 Causal Analysis Subsystem (`core/causal`)
- Enforces the DAG: Treatment -> Outcome with Confounders.
- Evaluates identification assumptions: Unconfoundedness, Positivity (common support), SUTVA.
- Methods: Difference-in-Differences (DiD), Propensity Score Weighting / Matching, OLS covariate adjustment.
- **Safety Fallback**: If assumptions fail (e.g. unobserved confounding suspected), automatically downgrades causal claim to associative/correlational with explicit warning banners.

#### 3.6 Dedicated Critic Agent (`core/critic`)
- Operates independently from the synthesis planner.
- Scans for:
  - Simpson's Paradox (trends reversing at sub-segment levels)
  - Survivorship & Selection Bias
  - Denominator Errors (changing customer baseline)
  - Temporal Leakage (using future data)
  - Multiple Testing / P-hacking (applies Bonferroni / Benjamini-Hochberg FDR)
  - Unsupported Causal Claims.
- Returns critique verdicts: `PASSED`, `WARNING`, or `REJECTED_REWORK_REQUIRED` with target state to return to.

#### 3.7 Calibrated Confidence & Evidence Store (`core/evidence`)
- **Evidence Object**: Hashes query SQL, query result dataset hash, timestamp, metric definition, and raw numbers.
- **Confidence Calibration Score (0.0 - 1.0)**:
  $$C = w_1 \cdot Q_{data} + w_2 \cdot S_{sample} + w_3 \cdot P_{stat} + w_4 \cdot G_{semantic} + w_5 \cdot E_{completeness}$$
- **Hallucination Guard**: Every quantitative claim in the generated text is scanned and regex-verified against the Evidence Store. Claims failing verification are stripped or flagged.

#### 3.8 Human-in-the-Loop (HITL) Subsystem (`core/hitl`)
- Pauses execution and persists state when:
  - Confidence < 0.70
  - Causal recommendation has high business risk
  - Ambiguity detected in question intent
  - Critic raises unresolved blocking risks.
- Resumes execution upon human approval, rejection, or plan adjustment.

#### 3.9 Backend API (`api/`)
- FastAPI application with asynchronous background worker support.
- Endpoints:
  - `POST /api/v1/analyses`: Launch new autonomous investigation.
  - `GET /api/v1/analyses/{id}`: Fetch analysis status, state machine progress, report.
  - `GET /api/v1/analyses/{id}/events`: Server-Sent Events (SSE) stream of real-time trajectory events.
  - `GET /api/v1/analyses/{id}/evidence`: Fetch all cryptographic evidence citations.
  - `POST /api/v1/analyses/{id}/approve`: Submit HITL decision.
  - `GET /api/v1/semantic/catalog`: Fetch semantic layer definitions.
  - `POST /api/v1/evaluations/run`: Run evaluation benchmark suite.

#### 3.10 Frontend Analyst Workspace (`frontend/`)
- Modern React + TypeScript SPA.
- Components:
  - Trajectory Stepper & State Machine Monitor
  - Real-time Event Feed
  - SQL & Query Cost Inspector
  - Hypothesis Tree & Bayesian Probabilities
  - Segment Contribution & Anomaly Explorer
  - Interactive Plotly Visualizer
  - Final Evidence-Backed Analyst Report Viewer with clickable citation popovers
  - HITL Review & Approval Modal.
