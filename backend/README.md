# Backend

FastAPI backend for shared expenses tracking, including cookie-based authentication foundation.

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

Auth-related environment defaults:

- `AUTH_COOKIE_NAME`: session cookie name
- `AUTH_COOKIE_SECURE`: use `true` in HTTPS environments
- `AUTH_COOKIE_SAMESITE`: defaults to `lax`
- `AUTH_SESSION_TTL_SECONDS`: Redis-backed session lifetime
- `AUTH_RESET_TOKEN_TTL_SECONDS`: password reset token validity window
- `AUTH_ENABLE_DEV_RESET_TOKEN_RESPONSE`: only for local/test workflows where email delivery is not wired yet
- `WORKSPACE_INVITATION_TTL_SECONDS`: workspace invitation validity window

## Implemented auth API

- `POST /api/v1/auth/sign-up`: create a user account
- `POST /api/v1/auth/sign-in`: validate credentials and issue the HTTP-only session cookie
- `POST /api/v1/auth/sign-out`: delete the Redis session and clear the cookie
- `GET /api/v1/auth/me`: resolve the current authenticated user from the cookie-backed session
- `POST /api/v1/auth/password-reset/request`: create a password reset token and return a generic success message
- `POST /api/v1/auth/password-reset/confirm`: rotate the password using a valid reset token

## Implemented workspace API

- `POST /api/v1/workspaces`: create a personal or shared workspace, owner membership, and default workspace categories for the creator
- `GET /api/v1/workspaces`: list the authenticated user's workspaces with their current role and member count
- `GET /api/v1/workspaces/{workspace_id}`: return workspace details for a member
- `PATCH /api/v1/workspaces/{workspace_id}`: update workspace name; owner only
- `GET /api/v1/workspaces/{workspace_id}/members`: list workspace members for any member
- `POST /api/v1/workspaces/{workspace_id}/invitations`: create an invitation; owner only
- `GET /api/v1/workspaces/{workspace_id}/invitations`: list workspace invitations; owner only
- `POST /api/v1/workspaces/{workspace_id}/invitations/{invitation_id}/revoke`: revoke a pending invitation; owner only
- `POST /api/v1/workspaces/invitations/accept`: accept an invitation token and create a member membership

## Implemented account API

- `POST /api/v1/workspaces/{workspace_id}/accounts`: create a workspace-scoped account for any workspace member
- `GET /api/v1/workspaces/{workspace_id}/accounts`: list active accounts with current balance for any workspace member
- `PATCH /api/v1/workspaces/{workspace_id}/accounts/{account_id}`: update an active account for any workspace member
- `POST /api/v1/workspaces/{workspace_id}/accounts/{account_id}/archive`: archive an account without deleting history for any workspace member

## Implemented category API

- `POST /api/v1/workspaces/{workspace_id}/categories`: create a workspace-scoped category for any workspace member
- `GET /api/v1/workspaces/{workspace_id}/categories`: list active categories by default for any workspace member
- `PATCH /api/v1/workspaces/{workspace_id}/categories/{category_id}`: update an active category for any workspace member
- `POST /api/v1/workspaces/{workspace_id}/categories/{category_id}/archive`: archive a category without deleting history for any workspace member

Implementation notes:

- session records are stored in Redis with a sliding TTL
- users and password reset tokens are stored in PostgreSQL
- workspaces, memberships, and invitations are stored in PostgreSQL
- accounts are stored in PostgreSQL and scoped to a workspace
- account names are unique per workspace only while active; archived names can be reused
- account balances are stored in integer minor units and `current_balance_minor` initially mirrors `initial_balance_minor`
- categories are stored in PostgreSQL and scoped to a workspace
- category names are unique per workspace and category type only while active; archived names can be reused
- new workspaces automatically receive a default category set, and the same seed logic is reused as an idempotent backfill path for older workspaces
- password hashes use PBKDF2-SHA256 with a configured pepper
- reset tokens are stored hashed and, in development/test, the plaintext token is included in the response for local workflows
- invitation tokens are stored hashed and, in development/test, the plaintext token is included in the invitation creation response for local workflows
- owner-only workspace actions return `403 Only workspace owners can perform this action.`
- non-member workspace actions return `403 You do not have access to this workspace.`
