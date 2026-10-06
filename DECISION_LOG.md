# Architecture Decision Log (ADR)

## ADR-001: Explicit Finite State Machine vs Free-Form LangChain Agent
- **Status**: Accepted
- **Context**: Autonomous agents that run unconstrained loops often suffer from non-deterministic behavior, infinite loops, and hallucinated progression.
- **Decision**: Implement an explicit 21-state machine with machine-checkable transition guards, bounded tool budgets, and strict phase gates (`OBSERVE -> INTERPRET -> PLAN -> ACT -> VERIFY -> CRITIQUE -> CORRECT -> REVERIFY -> RECORD -> CONTINUE`).
- **Consequences**: Deterministic predictability, auditability, ease of resumption, and foolproof human review checkpoints.

## ADR-002: Dual-Engine Data Warehouse (DuckDB + PostgreSQL)
- **Status**: Accepted
- **Context**: Heavy analytical queries (aggregations, window functions, time-series decompositions) require high performance, while transactional relational patterns mirror enterprise deployments.
- **Decision**: Use DuckDB as the primary high-speed in-process columnar analytical engine, coupled with a PostgreSQL connector for transactional replica queries. Both enforce strict read-only AST checks.
- **Consequences**: Instant local execution with zero heavyweight infrastructure dependencies, coupled with enterprise SQL dialect compatibility.

## ADR-003: sqlglot for AST-Level SQL Validation & Fanout Guards
- **Status**: Accepted
- **Context**: Regex-based SQL validation is easily bypassed and fails to detect subtle semantic bugs like join fanout or cartesian products.
- **Decision**: Use `sqlglot` to parse generated SQL into an Abstract Syntax Tree (AST). Programmatically verify that queries only contain `SELECT` expressions, that tables/columns match the semantic catalog, and that joined foreign keys conform to allowable cardinality without unaggregated multiplying joins.
- **Consequences**: Comprehensive defense against mutating queries, SQL injection, and semantic calculation errors.

## ADR-004: Defensive Causal Downgrading to Association
- **Status**: Accepted
- **Context**: AI models frequently mistake correlation for causation, producing dangerously misleading business claims (e.g. asserting a marketing campaign caused sales growth when seasonal trends were responsible).
- **Decision**: Require explicit identification assumption checks (unconfoundedness, common support, pre-treatment parallel trends). If any assumption is violated or cannot be empirically tested with available data, the subsystem deterministically downgrades the claim from causal to associative with prominent caveats.
- **Consequences**: Protects business users from unsound causal recommendations.

## ADR-005: Cryptographic Evidence Hashing & Numeric Verification
- **Status**: Accepted
- **Context**: LLMs can hallucinate numbers even when correct queries are run.
- **Decision**: Store every analytical finding in an immutable `EvidenceStore` with SHA-256 result hashes and metric lineage. A deterministic regex verifier cross-checks every numeric statement in the final report against the evidence store. Unverified numbers trigger critique failure and report revision.
- **Consequences**: Guarantees 100% citation coverage and eliminates unsupported numerical claims.
