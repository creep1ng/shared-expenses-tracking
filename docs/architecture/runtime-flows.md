# Runtime Flows

## Purpose

This document captures the key end-to-end flows that define the application's behavior.

At the current planning stage, these flows represent intended behavior and should be refined as implementation progresses.

## 1. Sign in flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL
    participant Redis as Redis

    User->>Frontend: Submit email and password
    Frontend->>Backend: POST /auth/login
    Backend->>DB: Validate user credentials
    Backend->>Redis: Create session record
    Backend-->>Frontend: Set secure session cookie
    Frontend-->>User: Redirect to workspace selection or dashboard
```

## 2. Workspace onboarding flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    User->>Frontend: Choose personal or shared workspace
    Frontend->>Backend: POST /workspaces
    Backend->>DB: Create workspace
    Backend->>DB: Create owner membership
    Backend-->>Frontend: Return workspace data
    Frontend-->>User: Show workspace home
```

## 3. Transaction creation flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    User->>Frontend: Submit transaction form
    Frontend->>Backend: POST /transactions
    Backend->>Backend: Validate session and workspace access
    Backend->>Backend: Validate account and category
    Backend->>Backend: Apply transaction business rules
    Backend->>DB: Persist transaction
    Backend->>DB: Recalculate affected account balance
    Backend-->>Frontend: Return created transaction and updated state
    Frontend-->>User: Show success and refreshed list/KPIs
```

## 4. Shared expense split flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    User->>Frontend: Create shared expense with split config
    Frontend->>Backend: POST /transactions with paid_by_user_id and split_config
    Backend->>Backend: Validate workspace membership and split rules
    Backend->>DB: Persist transaction
    Backend->>Backend: Recompute workspace net balance
    Backend-->>Frontend: Return transaction and net balance summary
    Frontend-->>User: Show updated shared balance widget
```

## 5. Settle-up flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    User->>Frontend: Trigger settle-up action
    Frontend->>Backend: POST /workspaces/{id}/settlements
    Backend->>Backend: Validate workspace role and current balance state
    Backend->>Backend: Create settlement movement or equivalent ledger effect
    Backend->>DB: Persist settlement result
    Backend->>Backend: Recompute net balance
    Backend-->>Frontend: Return updated balance state
    Frontend-->>User: Display cleared or reduced net balance
```

## Flow design notes

### Authentication

- session behavior is backend-owned
- the frontend should not be treated as the source of auth truth

### Financial correctness

- balance updates must happen as part of validated backend workflows
- split calculations must be deterministic and testable
- transfer logic must stay isolated from regular income/expense analytics

### Permissions

- all protected actions must validate workspace membership
- owner/member behavior must be enforced by the backend

## Future runtime flows to add

As new features are introduced, add sequence or flow diagrams for:

- invitation acceptance
- password reset
- receipt upload
- scheduled payment generation
- budget status recomputation
- forecast generation
