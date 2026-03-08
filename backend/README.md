# Backend

Minimal FastAPI backend skeleton for issue #36.

## Local commands

- Install dependencies: `uv sync --all-groups`
- Run API: `uv run uvicorn app.main:app --reload`
- Run tests: `uv run pytest`
- Run lint: `uv run ruff check .`
- Run format check: `uv run ruff format --check .`
- Run type check: `uv run mypy src tests`
- Run migrations: `uv run alembic upgrade head`

## Environment

Copy `.env.example` to `.env` and replace placeholder values such as `<db-user>` and `<db-password>` before running services that depend on Postgres.

If `backend/.env` is absent during bootstrap, local `make dev` falls back to the defaults declared in `.env.example`.
