.PHONY: test build run seed lint clean

PYTHON = .venv/bin/python
PYTEST = $(PYTHON) -m pytest

test:
	$(PYTEST) tests/ -v

test-fast:
	$(PYTEST) tests/test_semantic_layer.py tests/test_sql_engine.py tests/test_orchestrator.py tests/test_hypothesis.py tests/test_causal_critic.py tests/test_reports.py -v

build:
	cd frontend && npm run build

run: build
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf .pytest_cache frontend/dist
