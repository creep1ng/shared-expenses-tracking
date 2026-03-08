# ADR 0004: Store money in integer minor units

- Status: accepted
- Date: 2026-03-07

## Context

The application manages balances, expenses, transfers, and split calculations. Financial values must remain stable and predictable across storage, calculations, APIs, and presentation.

Using floating-point values for persisted money introduces avoidable precision and rounding risk.

## Decision

Persist monetary values in integer minor units.

Examples:

- `$10.50` becomes `1050` minor units
- currency remains explicit and separate from numeric storage

Formatting into user-facing decimal strings should happen at the API or UI presentation boundary, not in persistent storage.

## Rationale

- integer storage avoids floating-point precision errors
- split logic and balance math become easier to reason about
- financial invariants are easier to test

## Consequences

### Positive

- stable calculations
- simpler testing for exact balance results
- clearer backend domain rules

### Trade-offs

- developers must remember to convert at boundaries
- UI and API formatting logic must be explicit

## Alternatives considered

### Floating-point values

Rejected because they are a poor fit for financial persistence and exact arithmetic.

### Decimal storage as the default application representation

Possible in some systems, but integer minor units are simpler and more consistent for the planned architecture and API boundaries.
