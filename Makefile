# Colors
GREEN=\033[0;32m
BLUE=\033[0;34m
YELLOW=\033[0;33m
RED=\033[0;31m
CYAN=\033[0;36m
NC=\033[0m

export TERM=xterm-256color

.PHONY: setup-local setup-docker install run env pre-commit-install docker-up docker-logs tests-local tests-docker migrate upgrade downgrade lint format type-check help

setup-local: install pre-commit-install env
	@echo "$(GREEN)Local setup completed successfully!$(NC)"

setup-docker: env docker-up
	@echo "$(GREEN)Docker setup completed successfully!$(NC)"

install:
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

pre-commit-install:
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	poetry run pre-commit install --install-hooks
	@echo "$(GREEN)Pre-commit hooks installed successfully!$(NC)"

env:
	@if [ ! -f .env ]; then \
		if [ -f .env-example ]; then \
			echo "$(BLUE)Creating .env file from .env-example...$(NC)"; \
			cp .env-example .env; \
			echo "$(GREEN)  .env file created successfully$(NC)"; \
			echo "$(YELLOW)  Please update .env file with your actual values$(NC)"; \
		else \
			echo "$(RED)Error: .env-example file not found$(NC)"; \
			exit 1; \
		fi; \
	else \
		echo "$(CYAN).env file already exists$(NC)"; \
	fi

run:
	@echo "$(BLUE)Starting application...$(NC)"
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	@echo "$(BLUE)Starting Docker containers...$(NC)"
	docker compose up -d
	@echo "$(GREEN)Docker containers started successfully!$(NC)"

docker-logs:
	@echo "$(BLUE)Showing Docker logs...$(NC)"
	docker compose logs -f

tests-local:
	@echo "$(BLUE)Running tests locally...$(NC)"
	poetry run pytest -q

tests-docker:
	@echo "$(BLUE)Running tests in Docker (app service)...$(NC)"
	docker compose exec app poetry run pytest -q || (echo "$(RED)App container not running. Start with: make docker-up$(NC)" && exit 1)

lint:
	@echo "$(BLUE)Running ruff linter...$(NC)"
	poetry run ruff check app/

format:
	@echo "$(BLUE)Formatting code with ruff...$(NC)"
	poetry run ruff format app/
	poetry run ruff check --fix app/

type-check:
	@echo "$(BLUE)Running type checker (mypy)...$(NC)"
	poetry run mypy app/ --config-file=mypy.ini

migrate:
	@if [ -z "$(name)" ]; then \
		echo "$(RED)Usage: make migrate name=\"your migration message\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Generating Alembic revision...$(NC)"
	docker compose run --rm --workdir /app/app/database/migrations migrations poetry run alembic -c alembic.ini -n main revision --autogenerate -m "$(name)"
	@echo "$(GREEN)Migration created. Don't forget to commit changes.$(NC)"

upgrade:
	@echo "$(BLUE)Running Alembic upgrade to head in Docker...$(NC)"
	docker compose run --rm --workdir /app/app/database/migrations migrations sh /app/run-migrations.sh
	@echo "$(GREEN)Database upgraded successfully!$(NC)"

downgrade:
	@echo "$(BLUE)Running Alembic downgrade (one step)...$(NC)"
	docker compose run --rm --workdir /app/app/database/migrations migrations poetry run alembic -c alembic.ini -n main downgrade -1
	@echo "$(GREEN)Database downgraded one step.$(NC)"

db-shell:
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	docker compose exec postgres psql -U $${DATABASE__USER:-postgres} -d $${DATABASE__NAME:-answer_hub}

help:
	@echo "$(CYAN)BE Answer Hub - Available Commands$(NC)"
	@echo "$(CYAN)=====================================$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Development:$(NC)"
	@echo "  $(BLUE)setup-local$(NC)         Setup project for local development"
	@echo "  $(BLUE)setup-docker$(NC)          Setup project for Docker development"
	@echo "  $(BLUE)install$(NC)              Install dependencies with Poetry"
	@echo "  $(BLUE)pre-commit-install$(NC)   Install pre-commit hooks"
	@echo "  $(BLUE)env$(NC)                  Create .env file from .env-example"
	@echo "  $(BLUE)run$(NC)                  Run the FastAPI application locally"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@echo "  $(BLUE)docker-up$(NC)            Start all Docker containers"
	@echo "  $(BLUE)docker-logs$(NC)          Show Docker logs (follow mode)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  $(BLUE)tests-local$(NC)          Run tests locally"
	@echo "  $(BLUE)tests-docker$(NC)         Run tests inside Docker app container"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  $(BLUE)lint$(NC)                 Run ruff linter"
	@echo "  $(BLUE)format$(NC)               Format code with ruff"
	@echo "  $(BLUE)type-check$(NC)           Run mypy type checker"
	@echo ""
	@echo "$(GREEN)Database Migrations:$(NC)"
	@echo "  $(BLUE)migrate$(NC)              Generate Alembic revision (autogenerate)"
	@echo "                        Usage: make migrate name=\"add user table\""
	@echo "  $(BLUE)upgrade$(NC)              Run Alembic upgrade to head"
	@echo "  $(BLUE)downgrade$(NC)            Run Alembic downgrade (one step)"
	@echo "  $(BLUE)db-shell$(NC)             Open PostgreSQL shell"
	@echo ""
	@echo "$(GREEN)Help:$(NC)"
	@echo "  $(BLUE)help$(NC)                 Show this help message"
