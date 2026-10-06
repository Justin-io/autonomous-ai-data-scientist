# Evaluation Specification & Benchmark Suite

### 1. Benchmark Business Questions

The platform is evaluated against realistic enterprise analytical questions designed to test distinct analytical challenges:

#### BQ-1: Revenue Decline Root-Cause Analysis
- **Question**: *"Why did our total revenue decline by approximately 8% in Q3 2024 compared to Q2 2024?"*
- **Primary Mechanism**: Price hike on Enterprise tier leading to contract downgrades and elevated churn, coupled with a seasonal summer dip.
- **Expected Analytical Steps**:
  1. Ground metrics in Semantic Layer (`revenue`, `orders`, `calendar_dim`).
  2. Compute quarterly variance (-8.2%).
  3. Formulate competing hypotheses: (H1: Order volume dropped; H2: Average Order Value dropped; H3: Specific customer tier churned; H4: Refund surge).
  4. Perform shift-share segmentation by Customer Tier (`Enterprise` vs `SMB` vs `Consumer`).
  5. Identify Enterprise tier revenue drop explaining >70% of decline.
  6. Perform inferential statistics comparing pre/post cohorts.
  7. Confirm price adjustment date as change-point.
  8. Output cited report with waterfall chart.

#### BQ-2: Simpson's Paradox in Marketing Conversion
- **Question**: *"Did our new checkout redesign increase overall conversion rate, and should we roll it out to all users?"*
- **Trap**: Aggregate conversion rate appears higher in the treatment group (redesign), but within both Mobile and Desktop subgroups, conversion actually fell. The aggregate increase is entirely due to an imbalance in traffic allocation (more desktop traffic in treatment).
- **Expected Behavior**: Critic Agent and Statistical Engine must detect Simpson's paradox, flag the aggregated conclusion as misleading, conduct stratified analysis, and recommend against rollout without traffic balance.

#### BQ-3: Churn Surge & Refund Spike vs Seasonality
- **Question**: *"What caused the sharp increase in customer churn and refund requests in August 2024?"*
- **Primary Mechanism**: Release of a faulty product update on August 1st causing high refund rate in Product Category 'Pro Tools'.
- **Expected Behavior**: Anomaly detection identifies August 1st-7th spike; category segmentation isolates 'Pro Tools'; causal inference verifies refund surge preceded churn; observational limitation noted.

---

### 2. Evaluation Metrics

1. **Semantic Grounding Accuracy (SGA)**: % of metrics, dimensions, and entities correctly resolved against semantic catalog. Target: $\ge 98\%$.
2. **SQL Syntactic & Semantic Validity (SSV)**: % of generated SQL queries that are syntactically valid and conform to schema without execution error. Target: $100\%$.
3. **Execution Safety Rate (ESR)**: % of queries strictly read-only with no unauthorized schema access. Target: $100\%$.
4. **Unsupported Claim Rate (UCR)**: % of quantitative statements in final report lacking an explicit, verified link in the Evidence Store. Target: $0.0\%$.
5. **Citation Coverage Rate (CCR)**: % of key findings and numbers having cryptographic evidence IDs. Target: $100\%$.
6. **Simpson's Paradox Detection Rate (SPDR)**: Detection of subgroup reversal in BQ-2. Target: $100\%$.
7. **Causal Overreach Rate (COR)**: % of unverified observational associations claimed as causal. Target: $0.0\%$.
8. **Calibrated Confidence Score MSE**: Calibration of self-reported confidence against actual empirical accuracy. Target: $< 0.05$.
