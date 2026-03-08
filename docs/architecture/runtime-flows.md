# Runtime Flows

## Purpose

This document captures the key end-to-end flows that define the application's behavior.

Authentication flows below reflect the current implementation. Workspace onboarding and invitation acceptance also reflect the current implementation. Financial flows remain target-state and should be refined as those issues land.

## 1. Sign up flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    User->>Frontend: Submit email and password
    Frontend->>Backend: POST /api/v1/auth/sign-up
    Backend->>Backend: Normalize email and validate password length
    Backend->>DB: Ensure email is unique
    Backend->>DB: Create user with hashed password
    Backend-->>Frontend: Return created user payload
    Frontend-->>User: Continue to sign-in flow
```

## 2. Sign in flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL
    participant Redis as Redis

    User->>Frontend: Submit email and password
    Frontend->>Backend: POST /api/v1/auth/sign-in
    Backend->>DB: Validate user credentials and active status
    Backend->>Redis: Create auth:session:<session_id> entry with TTL
    Backend-->>Frontend: Set HTTP-only session cookie
    Frontend-->>User: Redirect to workspace selection or dashboard
```

## 3. Session persistence flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant Redis as Redis
    participant DB as PostgreSQL

    User->>Frontend: Open protected screen
    Frontend->>Backend: GET /api/v1/auth/me with session cookie
    Backend->>Redis: Load session payload by cookie value
    Backend->>DB: Load user by user_id from session payload
    Backend->>Redis: Refresh session TTL
    Backend-->>Frontend: Return authenticated user
    Frontend-->>User: Keep session active
```

Notes:

- the backend is the auth source of truth; the frontend only forwards the cookie
- if the cookie is missing, the Redis entry is gone, or the user is inactive, `/api/v1/auth/me` returns `401 Not authenticated.`

## 4. Sign out flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant Redis as Redis

    User->>Frontend: Trigger sign out
    Frontend->>Backend: POST /api/v1/auth/sign-out
    Backend->>Redis: Delete auth:session:<session_id>
    Backend-->>Frontend: Clear session cookie
    Frontend-->>User: Return to unauthenticated state
```

## 5. Password reset flow

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    User->>Frontend: Request password reset with email
    Frontend->>Backend: POST /api/v1/auth/password-reset/request
    Backend->>DB: Look up user by normalized email
    Backend->>DB: Delete expired tokens and revoke prior tokens for that user
    Backend->>DB: Store hashed reset token with expiry
    Backend-->>Frontend: Return generic success message
    Note over Backend,Frontend: In development/test, plaintext reset token is also returned
    User->>Frontend: Submit token and new password
    Frontend->>Backend: POST /api/v1/auth/password-reset/confirm
    Backend->>DB: Validate active token and update password hash
    Backend->>DB: Mark token as consumed
    Backend-->>Frontend: Return reset success message
```

## 6. Workspace onboarding flow

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

Notes:

- the creator always becomes the `owner` member of the workspace
- both personal and shared workspaces use the same membership model

## 7. Workspace invitation acceptance flow

```mermaid
sequenceDiagram
    actor Owner
    actor Invitee
    participant Frontend as Next.js Frontend
    participant Backend as FastAPI Backend
    participant DB as PostgreSQL

    Owner->>Frontend: Invite a user by email
    Frontend->>Backend: POST /workspaces/{workspace_id}/invitations
    Backend->>Backend: Validate authenticated owner membership
    Backend->>DB: Store hashed invitation token with expiry
    Backend-->>Frontend: Return invitation payload
    Invitee->>Frontend: Accept invitation while authenticated
    Frontend->>Backend: POST /workspaces/invitations/accept
    Backend->>Backend: Validate token, invited email, and expiry
    Backend->>DB: Create workspace member role=member
    Backend->>DB: Mark invitation accepted
    Backend-->>Frontend: Return workspace payload for the new member
```

## 8. Transaction creation flow

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

## 9. Shared expense split flow

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

## 10. Settle-up flow

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

### Local container entry flow

```mermaid
sequenceDiagram
    actor Contributor
    participant Proxy as nginx reverse proxy
    participant Frontend as Next.js container
    participant Backend as FastAPI container

    Contributor->>Proxy: Open http://localhost:8080/
    Proxy->>Frontend: Forward /
    Contributor->>Proxy: Call http://localhost:8080/api/
    Proxy->>Backend: Forward /api/
```

### Authentication

- session behavior is backend-owned and Redis-backed
- the session cookie is HTTP-only, with configurable `secure`, `samesite`, and optional `domain`
- password hashes use PBKDF2-SHA256 plus a configured pepper
- reset tokens are stored hashed in PostgreSQL and have a dedicated TTL

### Financial correctness

- balance updates must happen as part of validated backend workflows
- split calculations must be deterministic and testable
- transfer logic must stay isolated from regular income/expense analytics

### Permissions

- all protected actions must validate workspace membership
- owner/member behavior must be enforced by the backend
- current owner-only actions are workspace settings updates and invitation management

## Future runtime flows to add

As new features are introduced, add sequence or flow diagrams for:

- invitation acceptance
- receipt upload
- scheduled payment generation
- budget status recomputation
- forecast generation
