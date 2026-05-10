.PHONY: all setup setup-uv setup-backend setup-frontend setup-db setup-env setup-hooks \
        dev dev-backend dev-frontend dev-db \
        test test-backend test-frontend \
        lint format clean stop db-shell db-logs help

# Default target
all: help

# ============================================================
# SETUP
# ============================================================

## setup: Set up entire project from scratch
setup: setup-uv setup-env setup-backend setup-frontend setup-db setup-hooks
	@echo "Project setup complete. Run 'make dev' to start."

## setup-uv: Install uv if not already installed
setup-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "uv: $$(uv --version)"

## setup-backend: Set up Python backend with uv
setup-backend: setup-uv
	cd backend && uv sync --all-extras

## setup-frontend: Set up React frontend with npm
setup-frontend:
	cd frontend && npm install

## setup-db: Start database container and wait for readiness
setup-db: setup-env
	docker compose up -d db
	@echo "Waiting for database..."
	@until docker compose exec db pg_isready -U $${POSTGRES_USER:-hr_rag} 2>/dev/null; do \
		sleep 1; \
	done
	@echo "Database is ready."

## setup-hooks: Install git pre-commit hook
setup-hooks:
	git config core.hooksPath .githooks
	@echo "Git hooks installed."

## setup-env: Create .env files from examples if they don't exist
setup-env:
	@test -f .env || cp .env.example .env
	@test -f backend/.env || cp backend/.env.example backend/.env
	@test -f .mcp.json || cp .mcp.json.example .mcp.json
	@echo "Environment files ready."

# ============================================================
# DEVELOPMENT
# ============================================================

## dev: Run all services (database + backend + frontend)
dev: dev-db
	@trap 'kill 0' EXIT; \
		(cd backend && uv run uvicorn hr_rag.main:app --reload --host 0.0.0.0 --port 8000) & \
		(cd frontend && npm run dev) & \
		wait

## dev-backend: Run FastAPI backend with hot reload
dev-backend:
	cd backend && uv run uvicorn hr_rag.main:app --reload --host 0.0.0.0 --port 8000

## dev-frontend: Run Vite dev server
dev-frontend:
	cd frontend && npm run dev

## dev-db: Start database in background
dev-db:
	docker compose up -d db
	@until docker compose exec db pg_isready -U $${POSTGRES_USER:-hr_rag} 2>/dev/null; do \
		sleep 1; \
	done
	@echo "Database running on port $${POSTGRES_PORT:-5432}"

# ============================================================
# TESTING
# ============================================================

## test: Run all test suites
test: test-backend test-frontend

## test-backend: Run pytest with coverage
test-backend:
	cd backend && uv run pytest -v --cov=src/hr_rag

## test-frontend: Run vitest
test-frontend:
	cd frontend && npm test

# ============================================================
# LINTING
# ============================================================

## lint: Lint all code
lint:
	cd backend && uv run ruff check src/ tests/
	cd backend && uv run ruff format --check src/ tests/

## format: Auto-format code
format:
	cd backend && uv run ruff format src/ tests/
	cd backend && uv run ruff check --fix src/ tests/

# ============================================================
# DATABASE
# ============================================================

## db-migrate: Run all pending migrations
db-migrate:
	cd backend && uv run alembic upgrade head

## db-revision: Create a new migration (usage: make db-revision msg="add users table")
db-revision:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

## db-downgrade: Downgrade one migration
db-downgrade:
	cd backend && uv run alembic downgrade -1

## db-history: Show migration history
db-history:
	cd backend && uv run alembic history --verbose

## db-reset: Drop and re-create database, then run migrations
db-reset:
	docker compose exec db dropdb -U $${POSTGRES_USER:-hr_rag} --if-exists $${POSTGRES_DB:-hr_rag}
	docker compose exec db createdb -U $${POSTGRES_USER:-hr_rag} $${POSTGRES_DB:-hr_rag}
	docker compose exec db psql -U $${POSTGRES_USER:-hr_rag} -d $${POSTGRES_DB:-hr_rag} -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
	cd backend && uv run alembic upgrade head
	@echo "Database reset complete."

## db-shell: Open psql shell
db-shell:
	docker compose exec db psql -U $${POSTGRES_USER:-hr_rag} -d $${POSTGRES_DB:-hr_rag}

## db-logs: View database logs
db-logs:
	docker compose logs -f db

# ============================================================
# CLEANUP
# ============================================================

## stop: Stop all services
stop:
	docker compose down

## clean: Remove all generated files and containers
clean: stop
	docker compose down -v
	rm -rf backend/.venv
	rm -rf frontend/node_modules

# ============================================================
# HELP
# ============================================================

## help: Show available commands
help:
	@echo "HR-RAG Project Commands:"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  /'
