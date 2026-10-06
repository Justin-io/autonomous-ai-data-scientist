# Product Requirements Document (PRD)
## Autonomous AI Data Scientist Platform

### 1. Vision & Purpose
Build a production-grade Autonomous AI Data Scientist platform from scratch (not a toy chatbot or static demo). The platform autonomously investigates complex business questions (e.g., *"Why did our revenue decline 8% this quarter?"*), grounds itself in an enterprise semantic layer, formulates rigorous investigation plans, drafts and validates SQL, executes analytical queries, generates competing hypotheses, performs descriptive and inferential statistics, detects anomalies, conducts multi-dimensional segmentation, assesses causal vs. associative relationships, applies an independent Critic Agent, computes calibrated confidence scores, and produces fully cited, evidence-backed analyst reports with interactive visualizations.

---

### 2. Core Functional Requirements

#### 2.1 Natural Language Business Question Understanding & Semantic Grounding
- Accepts complex natural-language analytical questions.
- Grounding in an explicit Semantic Layer containing:
  - Canonical business entities (Customer, Order, Product, Subscription, Channel, etc.)
  - Metric definitions (Revenue, MRR, Churn Rate, AOV, Refund Rate, etc.) with SQL formulas and grain
  - Dimensions, hierarchies, and allowable joins (fanout prevention)
  - Business rules, synonyms, data freshness, and known caveats.
- Rejection or clarification of ambiguous questions lacking semantic support.

#### 2.2 Investigation Planning & Explicit State Machine
- Strict explicit state-machine orchestrator with state transitions:
  `QUESTION_RECEIVED` -> `INTENT_PARSED` -> `PLAN_CREATED` -> `SEMANTIC_GROUNDED` -> `SQL_DRAFTED` -> `SQL_VALIDATED` -> `QUERY_COST_ESTIMATED` -> `QUERY_EXECUTED` -> `DATA_PROFILED` -> `HYPOTHESES_GENERATED` -> `HYPOTHESES_RANKED` -> `HYPOTHESIS_TESTED` -> `SEGMENTS_ANALYZED` -> `ANOMALIES_DETECTED` -> `CAUSALITY_ASSESSED` -> `VISUALS_CREATED` -> `CRITIQUE_COMPLETED` -> `EVIDENCE_VERIFIED` -> `REPORT_DRAFTED` -> `HUMAN_REVIEW_REQUIRED` (conditional) -> `COMPLETE`.
- Closed execution policy: `OBSERVE -> INTERPRET -> PLAN -> ACT -> VERIFY -> CRITIQUE -> CORRECT -> REVERIFY -> RECORD -> CONTINUE`.
- Machine-checkable transition guards, retry budgets, timeout limits, and failure states.

#### 2.3 SQL Generation, Validation, Optimization & Dual-Engine Execution
- Read-only enforcement (AST-level parsing via `sqlglot`).
- AST & schema validation against database catalog.
- Join-cardinality checks, fanout detection, grain consistency, aggregation validation, null-handling, date boundaries, and denominator validation.
- EXPLAIN-based query cost estimation; predicate pushdown, partition pruning, aggregation reduction.
- Query timeout and row limits; intermediate result caching.
- Dual execution: DuckDB (fast in-process analytical columnar engine) and PostgreSQL.

#### 2.4 Autonomous Hypothesis Engine
- Generates multiple competing, falsifiable hypotheses.
- Ranks hypotheses by information gain and evidence requirements.
- Bayesian/probabilistic confidence updating as evidence is gathered.
- Explicit recording of rejected hypotheses with concrete falsification reasons.
- Prevention of premature convergence on superficial explanations.

#### 2.5 Statistical Analysis & Anomaly Detection
- Descriptive statistics, distributions, percentiles.
- Inferential statistics: two-sample t-tests, Mann-Whitney U, Chi-square, ANOVA, confidence intervals (95%, 99%), and effect sizes (Cohen's d, relative risk).
- Anomaly detection: robust statistical thresholds (IQR, Hampel filter), rolling z-scores, seasonal decomposition, isolation forests, and change-point detection.
- Multi-dimensional segmentation across customer, product, geography, acquisition channel, cohort, subscription tier; contribution analysis quantifying proportion of business movement explained.

#### 2.6 Causal Analysis Subsystem
- Explicit separation: Descriptive vs. Associative vs. Predictive vs. Causal.
- Observational causal inference techniques: Difference-in-Differences (DiD), propensity score matching, regression adjustment.
- Assumption checks: unconfoundedness/ignorability, positivity/common support, stable unit treatment value (SUTVA).
- Strict rule: Label conclusions as associative when unconfoundedness cannot be established; never present correlation as causation.

#### 2.7 Independent Critic Agent & Deterministic Verifiers
- Reviews analytical trajectory end-to-end.
- Actively identifies: Simpson's paradox, survivorship bias, selection bias, denominator errors, temporal leakage, multiple testing issues (Bonferroni / Benjamini-Hochberg FDR), p-hacking, overfitting, post-hoc storytelling, data drift, misleading charts, and unsupported causal claims.
- Forces rework loops to earlier states when severe analytical vulnerabilities are found.
- Deterministic verification wherever rules can be mathematically/programmatically proven.

#### 2.8 Calibrated Confidence & Evidence Grounding
- Calibrated confidence scoring combining: data quality, sample size, statistical significance, semantic layer alignment, model stability, and evidence completeness.
- Strict evidence citation: Every numerical claim in the final report must link to an evidence object with dataset hash, SQL query, metric definition, and calculation record.
- Unsupported or hallucinated claims must be detected, flagged, downgraded, or removed.

#### 2.9 Human-in-the-Loop (HITL) Approval Checkpoints
- Escalation triggered when: semantic ambiguity is material, evidence conflicts, confidence < threshold (e.g. < 0.70), high-stakes causal recommendations, sensitive data/PII, or query cost exceeds limit.
- UI exposes: interpreted question, proposed plan, semantic assumptions, SQL, cost, data quality, hypotheses, key evidence, rejected hypotheses, critic objections, and specific decision required.

#### 2.10 Evidence-Backed Analyst Report & Visualizations
- Executive answer, key findings, quantified revenue/metric impact, evidence table, hypothesis testing summary, segmentation breakdown, anomaly analysis, statistical test results, causal assessment, interactive Plotly visualizations, confidence breakdown, limitations, and recommendations.

#### 2.11 Synthetic Enterprise Analytics Warehouse & Scenarios
- Realistic schema: `customers`, `products`, `orders`, `order_items`, `subscriptions`, `payments`, `refunds`, `marketing_channels`, `calendar_dim`.
- Seeded benchmark business scenarios:
  1. Revenue decline due to pricing change and enterprise churn vs refund spike.
  2. Simpson's paradox across customer segments (aggregate conversion up, segment conversions down due to mix shift).
  3. Marketing channel degradation vs seasonality.
  4. Product mix cannibalization and margin erosion.
  5. Subscription churn spike post-feature deprecation.

#### 2.12 Evaluation Harness & Benchmark Suite
- Comprehensive benchmark business questions with ground-truth reasoning, required SQL, evidence, and known traps.
- Metrics: Grounding accuracy, SQL validity, execution success, numerical precision, statistical validity, unsupported claim rate (target: 0%), citation coverage (target: 100%), anomaly precision, causal validity, latency, and cost.

#### 2.13 React + TypeScript Workspace & FastAPI Backend
- Interactive analyst workspace with live trajectory stream, state diagram, SQL inspector, hypothesis tree, statistical cards, anomaly charts, Plotly visualizer, and approval modal.
- FastAPI backend with Pydantic v2 schemas, SSE/WebSocket streaming, asynchronous background jobs, OpenTelemetry tracing, and MLflow logging.

---

### 3. Non-Functional Requirements
- **Security**: Read-only DB connection, SQL AST sanitize, parameterization, PII redaction, indirect prompt injection defense (treating DB data as untrusted content).
- **Reproducibility**: Analysis runs saved with exact seeds, queries, data hashes, prompts, and parameter snapshots.
- **Portability**: Docker & Docker Compose setup, zero cloud hard-locking, AWS deployment architecture.
- **Performance**: Query timeout budgets, analytical processing under 60s for standard benchmark questions.
