.PHONY: verify test lint format audit clean help

PYTHON ?= python

help:
	@echo "TrafficTwin AI Makefile targets:"
	@echo "  make verify   - Run environment verification script"
	@echo "  make test     - Run pytest test suite"
	@echo "  make lint     - Run ruff linter check"
	@echo "  make format   - Run ruff format / auto-fix"
	@echo "  make audit    - Run bandit and pip-audit security scans"
	@echo "  make clean    - Clean caches and build artifacts"

verify:
	$(PYTHON) scripts/verify_environment.py

test:
	$(PYTHON) -m pytest tests/

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

audit:
	$(PYTHON) -m bandit -r backend sumo experiments scripts -c pyproject.toml --exclude "TrafficTwin References,.venv" || true
	$(PYTHON) -m pip_audit || true

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
