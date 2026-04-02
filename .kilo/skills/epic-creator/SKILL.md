---
name: epic-creator
description: >
  Guide the creation of a new epic for the shared-expenses-tracking project.
  Use this skill whenever the user wants to add a new feature, module, or
  major capability to the project — even if they don't use the word "epic".
  Trigger on phrases like "new feature", "add module", "plan functionality",
  "create user stories", "tech spec", "scaffold", or when the user describes
  a desired product behavior and needs a structured breakdown. This skill
  produces a tech spec, GitHub epic issue body, individual user story issues,
  code stubs, and test stubs — all ready for delegation to subagents.
---

# Epic Creator

You help the user go from a rough product idea to a fully specified epic with
delegable implementation tasks.

## Overview

The process has four phases:

1. **Discovery** — interview the user to understand the feature intent
2. **Validation** — check alignment with existing product docs
3. **Artifact generation** — produce all specs, issues, stubs, and tests
4. **Delegation plan** — create a task matrix for subagent worktree execution

Work through these phases sequentially. Do not skip the interview.

---

## Phase 1: Discovery Interview

The user will describe a feature idea, possibly vaguely. Your job is to extract
a structured understanding before writing anything.

### What to ask

Ask these questions (adapt wording naturally — don't read a script):

1. **User problem**: What problem does this solve? Who experiences it?
2. **Desired behavior**: What should the user be able to do after this is built?
3. **Scope boundaries**: What is explicitly NOT part of this epic?
4. **Workspace context**: Does this apply to personal workspaces, shared workspaces, or both?
5. **Data impact**: What new data does this feature need? What existing entities does it touch?
6. **API surface**: Roughly what endpoints or frontend flows are involved?
7. **JTBD**: Can you phrase this as 1–3 "jobs to be done" sentences?
8. **Dependencies**: Does this depend on other features being built first?
9. **ADR triggers**: Does this require any decisions that are hard to reverse?

Do NOT proceed to Phase 2 until the user has confirmed the answers. Summarize
what you understood and ask for explicit confirmation.

### Extract user stories

From the interview, decompose the epic into discrete user stories. Each user
story should:

- describe ONE user-facing capability
- have a clear "who / what / why" structure
- be independently implementable in a single branch/PR
- be small enough to complete in 1–3 days

If the user's idea is too large (many stories, complex dependencies), suggest
splitting into multiple epics.

---

## Phase 2: Validation Against Existing Docs

Before generating artifacts, read the current state of the project docs to
check alignment.

### Files to read

Read ALL of the following (in parallel if possible):

- `docs/product/vision.md` — product vision and principles
- `docs/product/scope.md` — MVP scope, delivery sequence, boundary rules
- `docs/product/glossary.md` — domain terminology
- `docs/architecture/data-model.md` — current entity model and invariants
- `docs/architecture/system-overview.md` — container responsibilities
- `docs/process/development-workflow.md` — branching, PR, and ADR rules
- All existing ADRs in `docs/adr/` — check for relevant decisions

### What to validate

- Does this epic align with the product vision and differentiator?
- Does it fit in the current scope (MVP, near-term, deferred)?
- Does it conflict with any existing scope decisions?
- Are there glossary terms that need updating or adding?
- Does the data model require changes? Are there existing ADRs that constrain this?
- Are there existing issues that overlap with this epic?

### Report findings

Tell the user:

- whether the epic fits the current scope or requires a scope update
- any glossary terms that should be added
- any ADRs that are relevant or need creating
- any conflicts with existing scope.md boundaries

If a scope update is needed, draft the change but do NOT modify scope.md yet.
Let the user decide when to apply it.

---

## Phase 3: Artifact Generation

After the user confirms the validated epic concept, generate all artifacts.
Create them in a single pass — do not stop between artifacts.

### 3a. Tech Spec

Create at `docs/architecture/epic-<slug>.md` where `<slug>` is a short
kebab-case identifier derived from the epic name.

Use the tech spec template from `references/tech-spec-template.md`.
Read that file and fill in every section based on the interview answers.

The tech spec MUST include:

- context and objectives (linking to vision.md)
- functional scope (capabilities list)
- non-functional requirements specific to this epic
- data model changes (new tables, columns, relationships — with Mermaid ER diagrams)
- API contracts (endpoint paths, methods, request/response shapes)
- runtime flow diagrams (Mermaid sequence diagrams for key flows)
- open questions and risks
- references to glossary terms and relevant ADRs

### 3b. GitHub Epic Issue

Generate the epic issue body as a markdown file at
`docs/architecture/epic-<slug>/epic-issue.md`.

Use the issue template from `references/epic-issue-template.md`.
This file is the content the user will paste into a GitHub issue.

The issue MUST include:

- summary with links to vision.md and scope.md
- goals and non-goals
- user segments and JTBD
- high-level capabilities
- link to the tech spec (relative path)
- dependencies and risks
- acceptance criteria (end-to-end, not per-US)
- placeholder section for related user stories (filled in after US creation)
- suggested labels and milestone

### 3c. User Story Issues

For each user story identified in Phase 1, generate a separate issue body file
at `docs/architecture/epic-<slug>/us-<id>-<short-slug>.md`.

Use the user story template from `references/user-story-template.md`.

Each user story issue MUST include:

- title: `US-<id>: <descriptive title>`
- user story statement (As a..., I want..., so that...)
- acceptance criteria (specific, testable, numbered)
- technical context:
  - which backend endpoints to create/modify (paths, methods)
  - which database changes (tables, columns, migrations)
  - which frontend components/pages to create/modify
  - which service/domain logic to implement
- API contract details (request/response schemas relevant to this US)
- data model impact (specific to this US, with Mermaid snippet if needed)
- test requirements (what to test, where, which layer)
- dependencies on other user stories (which US must be done first)
- references to the tech spec section

### 3d. Code Stubs

For each user story, generate skeleton code files that subagents can fill in.
Place them under `docs/architecture/epic-<slug>/stubs/us-<id>/`.

The stub structure follows the project's expected layout:

#### Backend stubs (if US involves backend work)

```
stubs/us-<id>/
  backend/
    app/
      api/
        routes/
          <resource>.py          # Route handler stubs with TODO comments
      services/
        <resource>.py            # Service layer stubs
      models/
        <resource>.py            # SQLAlchemy model stubs (if new entity)
      schemas/
        <resource>.py            # Pydantic schema stubs
    tests/
      api/
        test_<resource>.py       # API test stubs
      services/
        test_<resource>.py       # Service test stubs
```

#### Frontend stubs (if US involves frontend work)

```
stubs/us-<id>/
  frontend/
    src/
      app/
        <page>/
          page.tsx               # Page component stub
      components/
        <feature>/
          <component>.tsx        # Component stubs
      hooks/
        use-<feature>.ts         # Custom hook stubs
      lib/
        api/
          <resource>.ts          # API client stubs
```

#### Stub content rules

Every stub file MUST:

- contain the file path as a comment on line 1
- include TODO markers with specific implementation guidance
- reference the tech spec section that defines the behavior
- import from the correct packages (FastAPI, SQLAlchemy, Pydantic for backend; Next.js, React, shadcn/ui for frontend)
- NOT contain placeholder logic that could be mistaken for working code
- use typing annotations (Python) or TypeScript types (frontend)

Example backend route stub:

```python
# backend/app/api/routes/<resource>.py
# TODO: Implement routes for <resource> — see docs/architecture/epic-<slug>.md#api-contracts

from fastapi import APIRouter, Depends

router = APIRouter(prefix="/<resource>", tags=["<resource>"])

# TODO: GET /<resource> — list endpoint
# See tech spec section: <link>
# Requires: workspace membership dependency
# Returns: list of <resource> schemas

# TODO: POST /<resource> — create endpoint
# See tech spec section: <link>
# Requires: workspace membership dependency, request validation
# Returns: created <resource> schema, 201 status
```

### 3e. Test Stubs

Test stubs are included within the code stubs (see 3d), but also generate a
test plan document at `docs/architecture/epic-<slug>/test-plan.md`.

The test plan MUST include:

- test categories (unit, integration, e2e)
- per-user-story test scenarios
- which test files correspond to which US
- which tests require database fixtures vs mocks
- high-priority financial invariant tests (balance recalculation, split accuracy, etc.)

---

## Phase 4: Delegation Plan

After all artifacts are generated, create a delegation plan at
`docs/architecture/epic-<slug>/delegation-plan.md`.

This document enables parallel execution by subagents in worktrees.

### Delegation plan format

For each user story, create a delegation entry:

```markdown
### US-<id>: <title>

**Branch**: `us/<id>-<short-slug>` (from `epic/<slug>`)

**Depends on**: US-<X>, US-<Y> (or "none")

**Task description**:
<clear 2-3 sentence description of what the implementing agent must do>

**Files to read before starting**:
- docs/architecture/epic-<slug>.md#<relevant-section>
- docs/architecture/data-model.md
- docs/product/glossary.md
- <any other relevant docs>

**Files to create**:
- <list of files the agent should implement from stubs>

**Files to modify**:
- <list of existing files that need changes>

**Test requirements**:
- <specific test scenarios from test-plan.md>

**Acceptance criteria**:
- <copy the AC from the US issue>

**Definition of Done checklist**:
- [ ] All AC satisfied
- [ ] Tests written and passing
- [ ] Lint passes (ruff)
- [ ] Type checks pass (mypy)
- [ ] Docs updated if architecture changed
```

### Execution order

Analyze dependencies between user stories and produce an execution graph:

```markdown
## Execution order

### Wave 1 (parallel, no dependencies)
- US-1: ...
- US-3: ...

### Wave 2 (depends on Wave 1)
- US-2: depends on US-1
- US-4: depends on US-3

### Wave 3 (depends on Wave 2)
- US-5: depends on US-2, US-4
```

### Branching instructions

Include explicit git commands for the subagent workflow:

```markdown
## Branch setup

1. Create epic branch from main:
   git checkout -b epic/<slug> main

2. First commit: add tech spec and delegation plan:
   git add docs/architecture/epic-<slug>.md docs/architecture/epic-<slug>/
   git commit -m "docs: add epic-<slug> tech spec and delegation plan"

3. For each US, create feature branch from epic branch:
   git checkout -b us/<id>-<short-slug> epic/<slug>

4. After all US branches are merged into epic branch, open final PR:
   epic/<slug> → main
```

---

## Artifact Summary

After generating everything, present a summary to the user:

```
Generated artifacts for epic "<name>":

📄 Tech Spec
  docs/architecture/epic-<slug>.md

📋 GitHub Issues
  docs/architecture/epic-<slug>/epic-issue.md
  docs/architecture/epic-<slug>/us-1-<slug>.md
  docs/architecture/epic-<slug>/us-2-<slug>.md
  ...

🔧 Code Stubs
  docs/architecture/epic-<slug>/stubs/us-1/...
  docs/architecture/epic-<slug>/stubs/us-2/...

🧪 Test Plan
  docs/architecture/epic-<slug>/test-plan.md

🚀 Delegation Plan
  docs/architecture/epic-<slug>/delegation-plan.md

Next steps:
1. Review the tech spec and adjust if needed
2. Create the epic branch: git checkout -b epic/<slug> main
3. Commit the docs: git add docs/architecture/epic-<slug>.md docs/architecture/epic-<slug>/
4. Create GitHub issues from the generated bodies
5. Execute the delegation plan — assign subagents to waves
```

---

## Important rules

- Do NOT modify `docs/product/vision.md`, `docs/product/scope.md`, or `docs/product/glossary.md`
  during artifact generation. Flag what needs updating and let the user decide.
- Do NOT create git branches or commits. Only generate files.
- Do NOT run `gh` commands. Only generate issue body files.
- All generated markdown must be valid and renderable.
- All Mermaid diagrams must use correct syntax.
- All stub files must be syntactically valid Python/TypeScript even if incomplete.
- Use English for all generated content (matching existing docs).
- Reference `docs/product/glossary.md` terms consistently.
- Follow the project's naming conventions from AGENTS.md.
