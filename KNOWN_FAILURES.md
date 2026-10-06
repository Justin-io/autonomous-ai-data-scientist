# Known Failures & Lessons Learned Log

## Purpose
This log captures real bugs, failed tests, edge-case vulnerabilities, and lessons learned during implementation to prevent regression and document root cause resolutions.

| ID | Date | Component | Symptom | Root Cause | Resolution | Verified In |
|---|---|---|---|---|---|---|
| KF-001 | 2026-10-06 | PostgreSQL Daemon | Stale PID & stopped single-user initdb process | Process interrupted during manual test | Cleaned up stale locks, designed dual-engine connector prioritizing DuckDB embedded engine for instant local analytics and PostgreSQL when external cluster is available | Phase 1 Tests |
| KF-002 | 2026-10-06 | Pydantic Models | PydanticUserError: `BenchmarkCase` is not fully defined | Missing `Optional` in `typing` imports under `annotations` | Explicitly imported `Optional` from `typing` in `eval/benchmark_suite.py` | Phase 7 E2E Tests |
