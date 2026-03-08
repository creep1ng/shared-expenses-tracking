# ADR 0001: Record architecture decisions

- Status: accepted
- Date: 2026-03-07

## Context

The repository is starting from a greenfield state. Major decisions about stack, architecture, auth, money handling, deployment, and workflow will shape many future issues.

Without a consistent decision record, contributors and coding agents would be forced to rediscover context repeatedly, which increases drift and rework.

## Decision

The project will maintain Architecture Decision Records under `docs/adr/`.

ADRs are required for decisions that are:

- cross-cutting
- hard to reverse
- long-lived
- important for future contributors to understand

Each ADR should include:

- title
- status
- date
- context
- decision
- consequences
- alternatives considered

ADRs should be created or updated in the same branch as the change that introduces the decision when practical.

## Consequences

### Positive

- architectural reasoning becomes traceable
- future contributors can understand why the system is shaped a certain way
- issue implementation becomes more consistent

### Trade-offs

- contributors must spend time documenting important decisions
- some decisions may require updating older ADRs when superseded

## Alternatives considered

### Implicit decisions in PR descriptions only

Rejected because PR descriptions are less durable, harder to discover, and not structured enough for long-term architecture memory.

### Large architecture document without ADRs

Rejected because it tends to mix current state, future plans, and historical reasoning in one place, which makes decision history harder to audit.
