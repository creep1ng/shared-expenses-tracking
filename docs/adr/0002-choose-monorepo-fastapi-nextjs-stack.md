# ADR 0002: Choose monorepo FastAPI and Next.js stack

- Status: accepted
- Date: 2026-03-07

## Context

The product needs:

- a modern web frontend with structured forms and dashboard UI
- a backend that can safely own financial logic, validation, permissions, and session handling
- a clean path to local development and containerized deployment
- strong documentation, testing, and maintainability characteristics

## Decision

The repository will use a monorepo structure with:

- `frontend/` for a Next.js application using TypeScript, Tailwind CSS, and shadcn/ui, with Spanish (es) as the default language
- `backend/` for a FastAPI application using Python, Pydantic v2, SQLAlchemy 2.x, and Alembic

Primary supporting technologies:

- PostgreSQL for relational persistence
- Redis for session support and future short-lived infrastructure concerns
- Docker and Docker Compose for local and deployment-oriented environments

## Rationale

### Why Next.js + shadcn/ui

- fast path to a structured web UI
- strong support for forms, tables, and dashboard flows
- good developer experience with TypeScript
- shadcn/ui provides consistent, composable UI primitives without locking the project into a heavy component framework

### Why FastAPI

- clear API development model
- strong typing support with Pydantic
- suitable for structured backend services and validation-heavy workflows

### Why SQLAlchemy 2.x + Alembic

- mature relational modeling
- explicit control over data access patterns
- robust migration story for a financial domain

### Why a monorepo

- keeps frontend, backend, docs, and infrastructure changes aligned
- simplifies coordinated feature delivery
- helps agentic contributors update code and documentation together

## Consequences

### Positive

- clear separation between frontend and backend responsibilities
- strong typed contracts in both ecosystems
- good support for incremental growth
- straightforward Docker Compose local setup

### Trade-offs

- dual ecosystem maintenance: Python and TypeScript
- more tooling to bootstrap initially

## Alternatives considered

### Single-stack full Python web app

Rejected because the preferred product direction includes a modern frontend using shadcn/ui and a distinct frontend application experience.

### Full-stack JavaScript/TypeScript backend

Rejected because the approved backend direction is Python + FastAPI + Pydantic.

### Separate repositories for frontend and backend

Rejected because a monorepo better supports coordinated early-stage development, issue-driven delivery, and documentation updates.
