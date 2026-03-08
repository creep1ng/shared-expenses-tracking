SHELL := /bin/bash

COMPOSE ?= docker compose
PROJECT_NAME ?= shared-expenses-tracking
FRONTEND_DIR ?= frontend
BACKEND_DIR ?= backend
FRONTEND_PORT ?= 3000
BACKEND_PORT ?= 8000

.PHONY: help install dev dev-frontend dev-backend up down logs ps lint format typecheck test migrate ci

help:
	@printf "Available targets:\n"
	@printf "  make dev        Run frontend and backend locally with hot reload\n"
	@printf "  make up         Start full Docker Compose stack\n"
	@printf "  make down       Stop full Docker Compose stack\n"
	@printf "  make migrate    Apply Alembic migrations in backend container\n"
	@printf "  make lint       Run repo validation placeholder commands\n"
	@printf "  make format     Run repo formatting placeholder commands\n"
	@printf "  make typecheck  Run repo type-check placeholder commands\n"
	@printf "  make test       Run repo test placeholder commands\n"
	@printf "  make ci         Run lint, typecheck, and test\n"

install:
	@if [ -d "$(FRONTEND_DIR)" ]; then \
		pnpm --dir "$(FRONTEND_DIR)" install; \
	else \
		printf "Skipping frontend install: %s not present yet\n" "$(FRONTEND_DIR)"; \
	fi
	@if [ -d "$(BACKEND_DIR)" ]; then \
		uv sync --project "$(BACKEND_DIR)"; \
	else \
		printf "Skipping backend install: %s not present yet\n" "$(BACKEND_DIR)"; \
	fi

dev:
	@trap 'kill 0' EXIT; \
		$(MAKE) --no-print-directory dev-backend & \
		$(MAKE) --no-print-directory dev-frontend & \
		wait

dev-frontend:
	@if [ ! -d "$(FRONTEND_DIR)" ]; then \
		printf "Frontend workspace %s is not scaffolded yet\n" "$(FRONTEND_DIR)"; \
		exit 1; \
	fi
	@if [ ! -f "$(FRONTEND_DIR)/package.json" ]; then \
		printf "Frontend package manifest %s/package.json is missing\n" "$(FRONTEND_DIR)"; \
		exit 1; \
	fi
	pnpm --dir "$(FRONTEND_DIR)" dev

dev-backend:
	@if [ ! -d "$(BACKEND_DIR)" ]; then \
		printf "Backend workspace %s is not scaffolded yet\n" "$(BACKEND_DIR)"; \
		exit 1; \
	fi
	@if [ ! -f "$(BACKEND_DIR)/pyproject.toml" ]; then \
		printf "Backend project manifest %s/pyproject.toml is missing\n" "$(BACKEND_DIR)"; \
		exit 1; \
	fi
	@if [ ! -f "$(BACKEND_DIR)/.env" ]; then \
		printf "Backend .env not found; using bootstrap defaults from %s/.env.example\n" "$(BACKEND_DIR)"; \
	fi
	uv run --project "$(BACKEND_DIR)" uvicorn app.main:app --reload --host 0.0.0.0 --port "$(BACKEND_PORT)"

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

lint:
	@if [ -d "$(BACKEND_DIR)" ] && [ -f "$(BACKEND_DIR)/pyproject.toml" ]; then \
		uv run --project "$(BACKEND_DIR)" ruff check .; \
	else \
		printf "Skipping backend lint: backend project not scaffolded yet\n"; \
	fi
	@if [ -d "$(FRONTEND_DIR)" ] && [ -f "$(FRONTEND_DIR)/package.json" ]; then \
		pnpm --dir "$(FRONTEND_DIR)" lint; \
	else \
		printf "Skipping frontend lint: frontend project not scaffolded yet\n"; \
	fi

format:
	@if [ -d "$(BACKEND_DIR)" ] && [ -f "$(BACKEND_DIR)/pyproject.toml" ]; then \
		uv run --project "$(BACKEND_DIR)" ruff format .; \
	else \
		printf "Skipping backend format: backend project not scaffolded yet\n"; \
	fi
	@if [ -d "$(FRONTEND_DIR)" ] && [ -f "$(FRONTEND_DIR)/package.json" ]; then \
		pnpm --dir "$(FRONTEND_DIR)" exec prettier --write .; \
	else \
		printf "Skipping frontend format: frontend project not scaffolded yet\n"; \
	fi

typecheck:
	@if [ -d "$(BACKEND_DIR)" ] && [ -f "$(BACKEND_DIR)/pyproject.toml" ]; then \
		uv run --project "$(BACKEND_DIR)" mypy .; \
	else \
		printf "Skipping backend typecheck: backend project not scaffolded yet\n"; \
	fi
	@if [ -d "$(FRONTEND_DIR)" ] && [ -f "$(FRONTEND_DIR)/package.json" ]; then \
		pnpm --dir "$(FRONTEND_DIR)" exec tsc --noEmit; \
	else \
		printf "Skipping frontend typecheck: frontend project not scaffolded yet\n"; \
	fi

test:
	@if [ -d "$(BACKEND_DIR)" ] && [ -f "$(BACKEND_DIR)/pyproject.toml" ]; then \
		uv run --project "$(BACKEND_DIR)" pytest; \
	else \
		printf "Skipping backend tests: backend project not scaffolded yet\n"; \
	fi
	@if [ -d "$(FRONTEND_DIR)" ] && [ -f "$(FRONTEND_DIR)/package.json" ]; then \
		pnpm --dir "$(FRONTEND_DIR)" test; \
	else \
		printf "Skipping frontend tests: frontend project not scaffolded yet\n"; \
	fi

migrate:
	$(COMPOSE) run --rm backend sh -lc 'if [ -f alembic.ini ]; then alembic upgrade head; else printf "Missing backend/alembic.ini; scaffold backend before running migrations\\n"; exit 1; fi'

ci: lint typecheck test
