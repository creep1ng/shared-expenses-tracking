# ADR 0005: Model transactions, transfers, and balance recomputation

- Status: accepted
- Date: 2026-03-10

## Context

Issues `#30` and `#31` introduce the first durable ledger behavior for transactions and transfers.

This layer needs decisions that stay consistent across the database schema, backend validation, API contracts, analytics, and future shared-expense logic.

The implementation needed to answer four questions:

- how income, expense, and transfer movements are represented in storage
- how transfers relate to reporting and analytics
- how deletion behaves in the MVP
- how account balances stay correct after transaction writes

## Decision

Use one workspace-scoped `transactions` table for income, expense, and transfer movements.

- every row stores a `type`
- directional account references are explicit through `source_account_id` and `destination_account_id`
- income uses `destination_account_id`
- expense uses `source_account_id`
- transfer uses both account fields and does not use a category

Model transfers as first-class ledger movements, not as derived paired records.

- transfers remain visible in transaction history
- transfers are excluded from income and expense analytics

Use hard delete for transaction removal in the MVP.

- deleted transactions are removed from persistent storage rather than marked archived or soft-deleted

After every transaction create, update, or delete, recompute the affected account balances from transaction history.

- `current_balance_minor` is treated as a derived current-state value
- balance updates are not maintained through incremental deltas alone

## Rationale

- one table keeps the ledger model uniform for personal, shared, and transfer flows
- explicit directional account fields make validation and API behavior predictable
- first-class transfers preserve movement history without polluting expense or income reporting
- hard delete keeps the MVP simpler by avoiding tombstone rules, filtered uniqueness, and extra query branches
- recomputing from history prioritizes correctness and recovery from edge cases over premature write-path optimization

## Consequences

### Positive

- transaction APIs and backend services share one consistent movement model
- transfer behavior is explicit and easier to test than mirrored synthetic entries
- current balances can be restored from ledger history after any supported write
- future split and net-balance features can build on the same transaction record shape

### Trade-offs

- some columns are nullable depending on transaction type and must be guarded by service-layer validation
- hard delete removes an audit trail for deleted records in the MVP
- full balance recomputation adds extra database work on each write compared with pure delta updates
- analytics code must continue to respect transfer exclusion rules explicitly

## Alternatives considered

### Separate tables for income, expense, and transfer

Rejected because it would duplicate validation, complicate reads, and make shared transaction features harder to extend.

### Model transfers as paired income and expense rows

Rejected because it hides transfer intent, complicates reconciliation, and increases the risk of analytics drift.

### Soft delete transactions

Rejected for the MVP because it adds lifecycle complexity without a current product requirement for recovery or audit history.

### Incrementally mutate balances on each write

Rejected as the primary strategy because update and delete paths become easier to corrupt, while recomputation from history gives a simpler correctness model for the current scale.
