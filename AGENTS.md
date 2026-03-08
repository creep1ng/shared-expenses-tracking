# AGENTS.md

This file defines the operating contract for agentic coding agents and human contributors working in this repository.

The repository is currently in the pre-implementation phase. The codebase is still being bootstrapped, but the product direction, architecture decisions, workflow rules, and documentation expectations are already defined here.

## 1. Source of truth

- The GitHub repository issues in `creep1ng/shared-expenses-tracking` are the canonical source of product scope and feature intent.
- Do not invent major features outside the issue tracker unless the user explicitly requests it.
- If a change introduces a new architectural or process rule, update the appropriate docs in the same branch.

## 2. Product orientation

This application is a workspace-based expense tracking system for:

- personal finance management
- shared finances with a partner
- transaction registration and analysis
- net balance visibility for shared expenses

Primary product principle:

- a personal workspace is a one-member workspace
- a shared workspace uses the same domain model with multiple members

## 3. Mandatory workflow

This repository follows GitHub Flow.

Rules:

- branch from `main`
- keep branches focused and short-lived
- prefer one issue per branch unless changes are tightly coupled
- open a PR back into `main`
- keep `main` releasable

Recommended branch naming:

- `feature/<issue-number>-<short-slug>`
- `fix/<issue-number>-<short-slug>`
- `docs/<short-slug>`
- `adr/<short-slug>`
- `spike/<short-slug>`

If you need to create a TODO-list for multi-step implementations, make commits for each code step that implements code.

## 4. Shared Definition of Done

The following Definition of Done applies to all issues and must be treated as mandatory:

- [ ] Functionality: All the elements of the issue's Acceptance Criteria must be completed.
- [ ] Code: The code works, it runs locally and it's integrated on the goal branch without breaking the system.
- [ ] Quality: The code passes the linter, type checks and automated validations.
- [ ] Testing coverage: There are tests according to the change and all the required tests passes the CI validation.
- [ ] Bugs: There aren't critical bugs associated with the implementation.
- [ ] Docs: There were updated the technical documentation, README, API contracts, diagrams or use notes if the implementation requires it.

## 5. Definition of Ready expectations

Before implementation starts, an issue should be clear about:

- user or business problem
- acceptance criteria
- dependencies
- affected architecture, data, API, and UI areas
- whether an ADR is needed
- whether documentation or Mermaid diagrams are expected to change

## 6. Expected repository structure

The repository should evolve toward this shape:

```text
backend/
frontend/
docs/
  adr/
  architecture/
  process/
  product/
Makefile
docker-compose.yml
.env.example
README.md
AGENTS.md
```

Do not create ad hoc top-level folders when an existing location is appropriate.

## 7. Approved stack

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

### Tooling and quality

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

## 8. Architecture rules

- Treat the system as a monorepo with separate frontend and backend applications.
- Use a same-parent-domain deployment model by default.
- Prefer backend-issued secure cookie sessions over client-managed auth tokens in local storage.
- Put business rules in backend domain/service layers, not route handlers and not UI components.
- Model personal and shared use through the workspace abstraction.
- Store money in integer minor units, never floating-point values.
- Transfers must be represented as first-class transfer movements and excluded from income/expense analytics.
- Keep split logic simple in MVP. Do not prematurely implement itemized multi-segment transaction splitting unless explicitly required.

## 9. Documentation obligations

Documentation is part of implementation, not an optional afterthought.

Always assess whether a change affects:

- `README.md`
- `AGENTS.md`
- product docs
- API contracts
- architecture docs
- Mermaid diagrams
- ADRs

If a change affects architecture, data model, runtime flow, or contributor workflow, update docs in the same branch.

## 10. ADR policy

Create or update an ADR for decisions that are:

- difficult to reverse
- cross-cutting
- impactful to multiple future features
- important for future contributors to understand

Typical ADR topics include:

- stack choices
- auth strategy
- money representation
- session model
- deployment model
- data model rules
- authorization model
- background job approach

## 11. Mermaid rules

Mermaid is the default diagram format for this repository.

Use the appropriate diagram type:

- C4-style diagrams for system and container architecture
- ER diagrams for data model and schema relationships
- sequence diagrams for request and workflow interactions
- flowcharts for business decisions or process steps

Keep diagrams close to the docs they explain. Do not use external binary diagram assets unless unavoidable.

## 12. Code style expectations

### General

- Prefer clear, explicit code over clever code.
- Optimize for maintainability and auditability.
- Keep functions focused and side effects controlled.
- Avoid hidden coupling between frontend and backend logic.

### Python / FastAPI

- Use explicit typing on public functions, service methods, and data structures.
- Use Pydantic models for API contracts and validation.
- Use SQLAlchemy 2.x typed ORM patterns.
- Keep route handlers thin; move domain logic into services.
- Prefer dependency injection through FastAPI dependencies for infrastructure concerns.
- Raise domain-specific or HTTP-specific errors deliberately; do not swallow exceptions.
- Validate external input at boundaries.
- Use structured logging where relevant.

### TypeScript / Next.js

- Use TypeScript strictly; avoid `any` unless unavoidable and documented.
- Keep React components small and composable.
- Use Zod for form and API-boundary validation on the frontend where appropriate.
- Use server state libraries for remote data, not ad hoc global state.
- Avoid embedding business calculations in UI components.
- Favor semantic and accessible UI primitives.

## 13. Imports, formatting, naming, and types

### Imports

- Group imports by standard library, third-party, then local imports.
- Avoid circular dependencies.
- Prefer absolute or well-defined module imports over brittle deep relative chains.

### Formatting

- Python formatting should be handled by Ruff format.
- Frontend formatting should be handled by Prettier.
- Do not introduce style drift that conflicts with project tooling.

### Naming

- Use descriptive names that reflect domain intent.
- Python modules and functions: `snake_case`
- Python classes: `PascalCase`
- TypeScript variables/functions: `camelCase`
- React components and types: `PascalCase`
- Constants: `UPPER_SNAKE_CASE` when genuinely constant

### Types

- Avoid untyped public interfaces.
- Prefer narrow, explicit types to loose dictionaries and unstructured objects.
- Treat validation schemas and API models as part of the domain contract.

## 14. Error handling rules

- Handle expected business errors explicitly.
- Return clear, user-safe API errors for invalid actions and permission failures.
- Do not leak internal implementation details in API error responses.
- Validate authorization on protected workspace actions.
- Use confirmation flows for destructive actions in the UI.

## 15. Testing rules

- Write tests proportional to the change.
- Prioritize backend integration tests for financial workflows and authorization.
- Use frontend component tests for critical form and interaction behavior.
- Use Playwright for end-to-end happy-path user flows.
- Do not rely only on manual testing for financial logic.

High-priority test targets:

- authentication and session behavior
- workspace membership and permissions
- account balance recalculation
- transaction creation, editing, deletion, and transfers
- split logic and net balance computation

## 16. Planned command surface

The bootstrap should provide a stable root command interface through `make`.

Preferred targets:

- `make install`
- `make dev`
- `make up`
- `make down`
- `make lint`
- `make format`
- `make typecheck`
- `make test`
- `make migrate`

Until implementation exists, treat these as required targets to establish.

## 17. Single-test command patterns

These are the expected patterns once the project is scaffolded.

### Backend pytest

- file: `uv run pytest backend/tests/api/test_transactions.py`
- class: `uv run pytest backend/tests/api/test_transactions.py::TestCreateTransaction`
- test: `uv run pytest backend/tests/api/test_transactions.py::TestCreateTransaction::test_creates_expense`

### Frontend unit tests

- file: `pnpm --dir frontend vitest run src/components/transaction-form.test.tsx`
- named test: `pnpm --dir frontend vitest run src/components/transaction-form.test.tsx -t "submits equal split"`

### Playwright

- file: `pnpm --dir frontend playwright test tests/e2e/transactions.spec.ts`
- named test: `pnpm --dir frontend playwright test tests/e2e/transactions.spec.ts --grep "creates shared expense"`

## 18. Docker and Compose expectations

Docker and Docker Compose support is mandatory.

At minimum, local orchestration should support:

- `frontend`
- `backend`
- `db`
- `redis`

Use Dockerfiles and Compose definitions that support both local development and deployment-oriented reproducibility.

## 19. Issue implementation order

Recommended order:

1. environment/bootstrap and CI
2. authentication and sessions
3. workspace foundation and permissions
4. accounts and categories
5. transactions and transfers
6. dashboard KPI cards
7. shared-expense split logic and net balance
8. post-MVP enhancements

## 20. Rule about external instructions

If Cursor rules or Copilot instructions are added later in:

- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

they must be incorporated into this file and followed.

At the time of writing, no such files exist in this repository.
