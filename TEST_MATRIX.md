# Test Matrix

| Category | Suite | File | Tests / Targets | Status |
|---|---|---|---|---|
| Warehouse & Data | Synthetic Data Gen & Scenarios | `tests/test_warehouse.py` | Schema generation, foreign keys, reproducible anomalies (revenue drop, Simpson's paradox, refund spike) | PASSED (5/5) |
| Semantic Layer | Semantic Catalog & Lookups | `tests/test_semantic_layer.py` | Entity schema, metric validation, grain validation, allowable join graphs, synonym resolution | PASSED (5/5) |
| SQL Engine | AST Parser & Security | `tests/test_sql_engine.py` | Read-only enforcement, mutating query rejection, AST validation, fanout detection, EXPLAIN cost estimator | PASSED (7/7) |
| Orchestration | State Machine & Bounds | `tests/test_orchestrator.py` | 21-state transitions, machine guards, loop execution policy, budget limits, cancellation | PASSED (5/5) |
| Hypothesis | Competing Hypothesis Engine | `tests/test_hypothesis.py` | Multi-hypothesis generation, information gain ranking, Bayesian confidence updating, rejection logging | PASSED (3/3) |
| Statistics | Inferential & Anomaly Tools | `tests/test_statistics.py` | Two-sample t-test, Mann-Whitney, Chi-square, ANOVA, Cohen's d, Hampel/IQR anomaly detector, shift-share segmentation | PASSED (6/6) |
| Causal & Critic | Causal Inference & Critic Agent | `tests/test_causal_critic.py` | DiD estimation, assumption checking, Simpson's paradox trap detection, FDR multiple testing, associative downgrade | PASSED (4/4) |
| Evidence | Hashing & Verification | `tests/test_evidence.py` | SHA-256 data hashing, calibrated confidence calculation, deterministic numeric claim verifier, hallucination rejection | PASSED (4/4) |
| Visuals & Report | Plotly & Markdown Synthesis | `tests/test_reports.py` | Plotly spec generator, report citation validator, structured markdown renderer | PASSED (3/3) |
| API & System | FastAPI & End-to-End Benchmark | `tests/test_api_and_e2e.py` | FastAPI endpoints, SSE streaming events, HITL review endpoint, BQ-1 benchmark run | PASSED (4/4) |
