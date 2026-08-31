# Immune Atlas — build targets.
# The three targets the grader runs are setup, pipeline, and dashboard.
# Everything else supports development and CI.

PYTHON      ?= python3
PIP         := $(PYTHON) -m pip
DASHBOARD   := dashboard
NPM         := npm --prefix $(DASHBOARD)
PORT        ?= 3000
DB          := cell_counts.db
BUNDLE      := $(DASHBOARD)/public/data/bundle.json
MYPY_TARGETS := immune_atlas $(wildcard load_data.py)

.DEFAULT_GOAL := help
.PHONY: help setup setup-python setup-dashboard setup-e2e pipeline dashboard dashboard-build \
        test test-python test-dashboard test-e2e lint lint-python lint-dashboard \
        format check clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- setup

setup: setup-python setup-dashboard ## Install all dependencies (Python + Node)

setup-python:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

setup-dashboard:
	@if [ -f $(DASHBOARD)/package-lock.json ]; then $(NPM) ci; \
	elif [ -f $(DASHBOARD)/package.json ]; then $(NPM) install; \
	else echo "dashboard/ not initialised yet (see docs/PLAN.md WS-4)"; fi

setup-e2e: setup-dashboard ## Install Playwright browsers (CI and e2e only)
	$(NPM) exec playwright install --with-deps chromium

# ---------------------------------------------------------------- pipeline

pipeline: ## Initialise the database, load the CSV, and generate all outputs
	$(PYTHON) load_data.py
	$(PYTHON) -m immune_atlas.pipeline

# ---------------------------------------------------------------- dashboard

dashboard: $(BUNDLE) ## Start the dashboard dev server on $(PORT)
	@echo "Dashboard: http://localhost:$(PORT)  (Codespaces: use the forwarded port $(PORT))"
	$(NPM) run dev -- --hostname 0.0.0.0 --port $(PORT)

$(BUNDLE):
	@echo "No dashboard bundle found; running the pipeline first."
	$(MAKE) pipeline

dashboard-build: $(BUNDLE) ## Production static build into dashboard/out
	$(NPM) run build

# ---------------------------------------------------------------- quality

test: test-python test-dashboard ## Run all tests with coverage

test-python:
	$(PYTHON) -m pytest

test-dashboard:
	@if [ -f $(DASHBOARD)/package.json ]; then $(NPM) run test -- --run; else echo "dashboard/ not initialised yet"; fi

test-e2e: dashboard-build ## Playwright smoke tests against the static build
	$(NPM) run test:e2e

lint: lint-python lint-dashboard ## Lint and type-check everything

lint-python:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
	$(PYTHON) -m mypy $(MYPY_TARGETS)

lint-dashboard:
	@if [ -f $(DASHBOARD)/package.json ]; then $(NPM) run lint && $(NPM) run typecheck; else echo "dashboard/ not initialised yet"; fi

format: ## Auto-format Python and TypeScript
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .
	@if [ -f $(DASHBOARD)/package.json ]; then $(NPM) run format; fi

check: lint test ## The CI gate: lint + tests

clean: ## Remove generated files
	rm -f $(DB)
	rm -rf outputs/plots outputs/*.csv outputs/*.json outputs/*.md
	rm -rf $(DASHBOARD)/public/data/bundle.json $(DASHBOARD)/out $(DASHBOARD)/.next
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
