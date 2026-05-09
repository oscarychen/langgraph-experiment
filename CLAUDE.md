# HR-RAG Project

## Overview
Full-stack Retrieval-Augmented Generation (RAG) application for HR document Q&A.
- **Backend**: FastAPI + LangGraph + PostgreSQL/pgvector
- **Frontend**: React + Vite + Tailwind CSS + shadcn/ui + Zustand
- **LLM**: Google Gemini via langchain-google-genai

## Architecture
```
[React Frontend :5173] --HTTP--> [FastAPI Backend :8000] --SQL/pgvector--> [AlloyDB Omni :5432]
                                        |
                                 [LangGraph RAG Pipeline]
                                        |
                                 [Google Gemini API]
```

## Project Structure
- `backend/` - FastAPI app managed with uv (src layout: `src/hr_rag/`)
- `frontend/` - React Vite app managed with npm
- `db/init/` - Database initialization SQL scripts
- `docker-compose.yml` - Database service (AlloyDB Omni)

## Commands (via Makefile)
- `make setup` - Full project setup from scratch
- `make dev` - Start all services (DB + backend + frontend)
- `make dev-backend` - FastAPI with hot reload on :8000
- `make dev-frontend` - Vite dev server on :5173
- `make dev-db` - Start database container
- `make test` - Run all tests
- `make test-backend` - Run pytest with coverage
- `make test-frontend` - Run vitest
- `make lint` - Lint all code (ruff)
- `make format` - Auto-format code
- `make stop` - Stop all services
- `make clean` - Remove containers, volumes, venvs, node_modules
- `make db-shell` - Open psql shell
- `make db-logs` - Tail database logs

## Tech Stack
- Python 3.13+ (uv)
- FastAPI, Uvicorn, SQLAlchemy 2.0+ (asyncpg), pgvector
- LangGraph, LangChain, langchain-google-genai
- React 19, Vite, TypeScript
- Zustand (state), Tailwind CSS v4, shadcn/ui
- AlloyDB Omni / PostgreSQL + pgvector (Docker)

## Conventions

### Backend
- Use `uv run` for all Python commands
- Async endpoints with `async def`
- Pydantic v2 for validation and settings
- Source in `backend/src/hr_rag/`, imports as `hr_rag.*`
- Ruff for linting/formatting (line-length 88)
- pytest with asyncio auto mode

### Frontend
- npm for package management
- `@/` path alias maps to `src/`
- Components: `src/components/`, Pages: `src/pages/`
- shadcn/ui components in `src/components/ui/`
- Zustand stores in `src/stores/`
- API calls in `src/services/`
- Vitest + React Testing Library for tests

### Database
- AlloyDB Omni Docker image for local dev
- pgvector for vector storage (768-dim for Google embeddings)
- Init scripts in `db/init/`
- Connection: `postgresql+asyncpg://`

### Git
- Conventional commits (feat:, fix:, chore:, docs:, test:, refactor:)
- Never commit `.env`, `.mcp.json`, or `node_modules/`
- Pre-commit hook in `.githooks/pre-commit` runs ruff (backend) and eslint+tsc (frontend) on staged files
- Install hooks: `make setup-hooks` (included in `make setup`)

## Environment Variables
See `.env.example`. Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_API_KEY` - Google AI API key for Gemini
- `POSTGRES_USER/PASSWORD/DB` - Database credentials
