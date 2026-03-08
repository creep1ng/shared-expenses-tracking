# Development Workflow

## Workflow model

This project uses GitHub Flow.

The default branch is `main`, and it should remain in a releasable state.

## Core principles

- start from a GitHub issue
- work in a short-lived branch
- keep changes focused
- update code and docs together when required
- merge only after validation and review

## Standard feature workflow

### 1. Start from an issue

Before implementation begins:

- confirm the issue is sufficiently defined
- verify dependencies and scope
- determine whether an ADR is required
- determine which docs and diagrams are affected

If the issue is not ready, refine it before coding.

### 2. Create a branch from `main`

Use focused branch names:

- `feature/26-authentication-session-management`
- `feature/30-transactions-crud-foundation`
- `fix/31-transfer-balance-recalculation`
- `docs/update-runtime-flows`
- `adr/cookie-session-auth`

### 3. Implement incrementally

Implementation should:

- follow the approved stack and ADRs
- preserve a clean architecture boundary between frontend and backend
- include tests proportional to the change
- update documentation in the same branch when relevant

### 4. Open a pull request

Every PR should include:

- linked issue
- concise implementation summary
- notes about migrations or environment changes
- test evidence
- documentation impact summary
- ADR impact summary if relevant

### 5. Validate before merge

Before merge, ensure:

- lint passes
- type checks pass
- automated tests pass
- required docs are updated
- the issue's acceptance criteria are satisfied

## Issue categories

Common issue types for this project:

- feature
- enhancement
- bug
- docs
- tech-debt
- spike
- ADR decision item

## Documentation in the workflow

Documentation is expected to evolve with the system.

Update docs when a change affects:

- architecture boundaries
- data model
- runtime flows
- API contracts
- contributor workflow
- product scope or glossary

Do not postpone all docs until the end of a milestone.

## ADR trigger points

Create or update an ADR when a change introduces a decision that is:

- structural
- long-lived
- cross-cutting
- hard to reverse

Examples:

- auth strategy
- money representation
- monorepo structure
- deployment topology
- background processing model

## Recommended PR checklist

- issue linked
- acceptance criteria satisfied
- tests added or updated
- lint and type checks pass
- migrations reviewed if present
- docs updated if behavior or architecture changed
- ADR created or updated if needed

## Root command contract

The repository root owns the shared operational command surface through `make`.

Required semantics:

- `make dev`: runs frontend and backend locally with hot reload, outside Docker Compose
- `make up`: starts the full Docker Compose topology, including reverse proxy and backing services
- `make down`: stops the Docker Compose topology
- `make migrate`: applies Alembic migrations in the backend runtime context

Supporting commands such as `lint`, `format`, `typecheck`, `test`, and `ci` should remain rooted at the repository top level so contributors and CI use the same interface.

This split keeps day-to-day application development fast while preserving a reproducible full-stack Docker path for integration and preview environments.

## Release philosophy

Prefer merging smaller validated increments over large multi-concern branches.

The goal is to keep `main` healthy and make the implementation history easy to follow.
