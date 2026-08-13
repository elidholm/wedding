.DEFAULT_GOAL := help

.PHONY: help install fmt fmt-check lint lint-fix html-lint check test ci run dev run-local docker docker-up docker-down docker-logs clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Sync all dependencies (runtime + dev) via uv
	uv sync --all-extras --dev

fmt: ## Auto-format the codebase with ruff and isort
	uv run isort .
	uv run ruff format .

fmt-check: ## Check formatting without writing changes (CI parity)
	uv run ruff format --check .

lint: ## Lint the codebase with ruff
	uv run ruff check .

lint-fix: ## Lint and auto-fix what ruff can fix
	uv run ruff check --fix .

html-lint: ## Lint the HTML templates with djlint
	uv run djlint . --profile=jinja

check: ## Type-check the codebase with mypy
	uv run mypy .

test: ## Run the unit test suite with pytest
	uv run pytest

ci: fmt-check lint check test html-lint ## Run fmt-check + lint + typecheck + test + html-lint (pre-push CI gate)

run: ## Tear down and spin up the app via Docker Compose (./run.sh)
	./run.sh

dev: ## Tear down and spin up the app in development mode via Docker Compose (./run.sh)
	./run.sh -d

stop: ## Stop and remove containers via Docker Compose (./run.sh)
	./run.sh -s

run-local: ## Run the app directly with uv, without Docker
	uv run python src/main.py

docker: ## Build the Docker image
	docker compose build

docker-up: ## Start containers in the background
	docker compose up -d

docker-down: ## Stop containers and remove orphans
	docker compose down --remove-orphans

docker-logs: ## Follow container logs
	docker compose logs -f

clean: ## Remove regenerable caches (__pycache__, ruff/pytest caches)
	find . -type d -name '__pycache__' -not -path './.venv/*' -exec rm -rf {} +
	rm -rf .ruff_cache .pytest_cache
