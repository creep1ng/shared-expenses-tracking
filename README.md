# shared-expenses-tracking

Shared expenses tracking is a workspace-based personal finance application focused on two complementary use cases:

- managing personal finances in a structured way
- managing shared expenses with a partner, including split logic and settlement visibility

The repository is currently in the pre-implementation phase. This documentation baseline defines the product scope, engineering constraints, architecture direction, and contributor workflow before application code is introduced.

## Product intent

The product should allow users to:

- create a personal workspace or a shared workspace
- register financial movements against real accounts and categories
- analyze balances, income, expenses, and cash flow
- track partner-oriented shared expenses and understand who owes whom

The GitHub issue tracker in `creep1ng/shared-expenses-tracking` is the canonical source of backlog scope and feature intent.

## Planned stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Hook Form
- Zod
- TanStack Query
- **Language: Spanish (es)**

### Backend

- Python 3.13
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis

### Quality and tooling

- uv
- Ruff
- mypy
- pytest
- Vitest
- Playwright

### Infrastructure

- Docker
- Docker Compose
- GitHub Actions

## Architecture summary

The application will be built as a monorepo with:

- `frontend/` for the Next.js web application
- `backend/` for the FastAPI API and domain logic
- `docs/` for product, process, ADR, and architecture documentation

The default deployment topology is:

- same parent domain for frontend and backend
- reverse proxy routing to the frontend and backend services
- backend-issued secure cookie sessions

Core design assumptions:

- a personal workspace is implemented as a one-member workspace
- shared finance flows build on the same workspace model
- money is stored in integer minor units
- business logic belongs in backend services, not in UI components

## MVP scope

The initial MVP is intentionally limited to the minimum feature set required to deliver real value.

Included in MVP:

- authentication and session management
- personal and shared workspace onboarding
- workspace roles and permissions
- accounts CRUD
- categories CRUD
- transactions CRUD
- transaction-to-account and transaction-to-category linkage
- transfers between accounts
- dashboard base KPI cards
- basic partner split support and net balance calculation

Deferred until post-MVP:

- advanced metadata and receipts
- budgets and forecasts
- scheduled payments
- debt tracking
- advanced charts
- complex split transaction segmentation

Details are documented in `docs/product/scope.md`.

## Documentation map

- `AGENTS.md`: operating instructions for agentic contributors and implementation rules
- `docs/product/vision.md`: product goals, target users, and constraints
- `docs/product/scope.md`: MVP and post-MVP scope boundaries
- `docs/product/glossary.md`: shared business vocabulary
- `docs/process/`: workflow, DoR, DoD, and documentation standards
- `docs/adr/`: architecture decision records
- `docs/architecture/`: architecture overview, data model, and runtime flows

## Delivery workflow

This project follows GitHub Flow:

- create or refine a GitHub issue first
- branch from `main`
- implement in a focused branch
- update code and documentation in the same PR when required
- merge back to `main` once checks and review are complete

Every issue shares a common Definition of Done, documented in:

- `AGENTS.md`
- `docs/process/definition-of-done.md`

## Implementation roadmap

### Phase 0: documentation baseline

- ADR process and initial foundational ADRs
- product, workflow, and architecture docs
- contributor guidance in `AGENTS.md`

### Phase 1: platform bootstrap

- monorepo scaffolding
- Docker and Compose support
- backend and frontend project setup
- linting, type checking, testing, and CI

### Phase 2: foundation features

- authentication and sessions
- workspace model and invitations
- roles and permissions

### Phase 3: financial ledger core

- accounts
- categories
- transactions
- transfers

### Phase 4: shared-expense value layer

- split configuration
- net balance calculation
- settle-up flow
- dashboard KPI cards

## Local setup and infrastructure baseline

The repository now includes the root infrastructure contract for the bootstrap phase.

Current scope of this baseline:

- root `Makefile` defining the expected command surface
- root `docker-compose.yml` with `proxy`, `frontend`, `backend`, `db`, and `redis`
- `.env.example` documenting runtime defaults
- GitHub Actions workflows for pull request validation and preview image publishing
- nginx reverse proxy config for same-parent-domain routing in local Docker Compose

This is intentionally a minimal runnable skeleton for infrastructure and documentation. Application internals in `frontend/` and `backend/` are still expected to be scaffolded in follow-up issues.

## Command surface

The repository standardizes a Docker-first split command model:

- `make dev`: run frontend and backend locally with hot reload
- `make up`: run the full Docker Compose topology in the background
- `make down`: stop the full Docker Compose topology and remove orphan containers
- `make migrate`: execute Alembic migrations in the backend container
- `make lint`: run backend and frontend lint commands when those projects exist
- `make format`: run backend and frontend formatting commands when those projects exist
- `make typecheck`: run backend and frontend type checks when those projects exist
- `make test`: run backend and frontend tests when those projects exist
- `make ci`: run `lint`, `typecheck`, and `test`

Until `frontend/` and `backend/` are scaffolded, the non-Docker validation targets intentionally skip missing application workspaces instead of failing on absent manifests.

## Local topology

The default local Docker topology is:

- `proxy`: nginx entrypoint exposed on `localhost:8080`
- `frontend`: Next.js container behind the reverse proxy
- `backend`: FastAPI container behind the reverse proxy
- `db`: PostgreSQL for application persistence
- `redis`: Redis for session and short-lived runtime state

Traffic model:

- `/` routes to the frontend service
- `/api/` routes to the backend service
- direct database and Redis ports remain published for local inspection and tooling

## Environment bootstrap

1. Copy `.env.example` to `.env`.
2. Replace placeholder values such as `<db-user>` and `<db-password>` with local development credentials, then adjust image tags or ports if needed.
3. Use `make up` for the containerized stack.
4. Use `make dev` once dependencies are installed; for the bootstrap backend it runs with `backend/.env.example` defaults when `backend/.env` is absent.

## CI and preview images

Two root workflows are defined:

- `.github/workflows/ci.yml`: validates Compose configuration and the root command surface on pull requests to `main`
- `.github/workflows/docker-preview.yml`: builds and publishes preview images to GHCR when component Dockerfiles exist

Preview publication behavior:

- pushes to `main` publish branch and SHA tags
- pull requests from the same repository can publish PR preview tags
- pull requests from forks build without push
- if `frontend/Dockerfile` or `backend/Dockerfile` is not present yet, the corresponding image job is skipped cleanly

## Migration expectation

`make migrate` is reserved for Alembic schema application and should run `alembic upgrade head` inside the backend container.

The infrastructure baseline assumes the backend bootstrap will add:

- `backend/alembic.ini`
- `backend/alembic/`
- a minimal baseline revision that can be applied in empty environments

## Current implementation status

This repository is no longer docs-only. It now has the root-level infrastructure and workflow contract needed for the full bootstrap, while application services remain to be implemented in the backend and frontend worktrees.
