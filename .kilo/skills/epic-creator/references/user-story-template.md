# User Story Issue Template

<!-- This file is the body of a GitHub user story issue -->
<!-- Replace all <placeholders> with actual content -->
<!-- Remove this comment block before pasting into GitHub -->

## User Story

**As a** <user role>,
**I want to** <action>,
**so that** <benefit>.

**Epic**: `EPIC: <Epic Name>` (parent issue)
**Tech Spec**: [`docs/architecture/epic-<slug>.md#<section>`](../docs/architecture/epic-<slug>.md#<section>)

---

## Acceptance Criteria

<!-- Each criterion must be specific, testable, and verifiable -->

- [ ] <AC 1: describe the expected behavior>
- [ ] <AC 2: describe the expected behavior>
- [ ] <AC 3: describe edge case or error handling>
- [ ] <AC 4: describe data validation or invariant>

---

## Technical Context

### Backend changes

**Endpoints to create/modify**:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/<resource>` | <what it does> |
| `GET` | `/api/<resource>` | <what it does> |

**Service/domain logic**:
- <Service method 1: what it computes or orchestrates>
- <Service method 2>

**Database changes**:
- <New table or column: table.column — type — nullable/required>
- <Migration: Alembic revision description>

### Frontend changes

**Pages/screens**:
- <Page route: what it displays>

**Components**:
- <Component name: what it renders, what interactions it supports>

**API integration**:
- <Which API endpoints the frontend calls>

---

## API Contract Details

<!-- Request/response schemas specific to this user story -->

### `POST /api/<resource>`

**Request**:
```json
{
  "field": "value_type"
}
```

**Response** (201):
```json
{
  "id": "uuid",
  "field": "value"
}
```

**Validation rules**:
- <field>: <validation rule>

---

## Data Model Impact

<!-- Specific to this user story, not the whole epic -->

**Table**: `<table_name>`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `id` | UUID | No | Primary key |
| `workspace_id` | UUID | No | FK to workspaces |
| `<field>` | <type> | <Yes/No> | <purpose> |

**Invariants**:
- <Invariant specific to this user story>

---

## Test Requirements

### Backend tests

| Test file | Test scenarios |
|-----------|---------------|
| `tests/api/test_<resource>.py` | <scenario 1>, <scenario 2> |
| `tests/services/test_<resource>.py` | <scenario 1>, <scenario 2> |

**High-priority tests**:
- <Financial invariant test: e.g., "balance recalculation after operation">
- <Authorization test: e.g., "non-member cannot access resource">
- <Edge case test: e.g., "concurrent updates handled correctly">

### Frontend tests

| Test file | Test scenarios |
|-----------|---------------|
| `src/components/<feature>/<component>.test.tsx` | <scenario 1>, <scenario 2> |

---

## Dependencies

**Depends on**: <list US IDs that must be completed first, or "none">

**Blocks**: <list US IDs that cannot start until this is done, or "none">

---

## Definition of Done

- [ ] All acceptance criteria satisfied
- [ ] Backend endpoints implemented and tested
- [ ] Frontend components implemented and tested (if applicable)
- [ ] Database migration created and tested
- [ ] Tests pass: `uv run pytest` (backend) / `pnpm --dir frontend vitest run` (frontend)
- [ ] Lint passes: `uv run ruff check` / `pnpm --dir frontend lint`
- [ ] Type checks pass: `uv run mypy` / `pnpm --dir frontend typecheck`
- [ ] Docs updated if architecture behavior changed
- [ ] No critical bugs
