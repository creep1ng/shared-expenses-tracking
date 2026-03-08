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

## Local setup status

Application bootstrap has not started yet. Setup instructions will be added once the initial monorepo, Docker configuration, and command surface are implemented.

Until then, this repository should be treated as a documentation-first planning baseline for the upcoming implementation.
