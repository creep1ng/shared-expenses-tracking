# ADR 0006: Computed net balance strategy

- Status: accepted
- Date: 2026-03-22

## Context

Shared workspaces need a net balance view that shows how much each member owes or is owed after shared expenses are split. This value drives settlement prompts, dashboards, and the core value proposition of shared-finance features.

Several storage strategies exist for derived values like net balance. The choice affects read performance, write complexity, data freshness, and how well the approach aligns with the patterns already established in ADR 0005.

Key constraints for MVP:

- the split configuration for each transaction is stored in a `split_config` JSON field on the transaction record, capturing the split type and participant shares
- net balances are per-currency; cross-currency netting is out of scope for MVP
- transfers must be excluded from net balance computation, consistent with their exclusion from income and expense analytics
- the system should remain simple enough for couple-scale workloads without premature infrastructure

## Decision

Compute net balances from transaction history on each read using database queries.

- no materialized views, persistent summary tables, or background jobs are used for net balance
- the query joins workspace transactions with their `split_config` data to derive per-member shares and aggregate the net position
- the result is a real-time calculation with no staleness window
- this mirrors the "recompute from history" pattern already used for `current_balance_minor` in ADR 0005

## Rationale

- **Simplicity.** Computed queries avoid the need for refresh pipelines, trigger chains, or cache invalidation logic. The read path is the only path that needs to be correct.
- **Correctness.** Recomputing from the canonical transaction history guarantees the net balance always reflects the current state of the ledger, including recent creates, updates, and deletes.
- **Consistency.** This approach aligns directly with ADR 0005's decision to recompute account balances from history rather than maintain incremental deltas. Applying the same principle to net balance keeps the system's mental model uniform.
- **Low coupling.** No extra tables or materialized views means fewer schema objects to migrate, index, and keep in sync as the domain model evolves.

## Consequences

### Positive

- net balance is always current with no staleness window
- no refresh infrastructure, background jobs, or cron schedules to maintain
- schema changes to transactions or split_config do not require migrating a separate summary table
- the approach scales naturally as the query logic evolves during early product iteration

### Trade-offs

- every net-balance read pays a CPU and I/O cost proportional to the workspace's transaction history
- aggregate queries may become a bottleneck at very high transaction volumes, but couple-scale workloads are well within acceptable performance for MVP
- caching at the application or HTTP layer can be added later without changing the underlying query strategy

## Alternatives considered

### Materialized view

Rejected because it introduces a refresh strategy (manual, scheduled, or incremental) that adds operational complexity without a clear performance need at MVP scale. Stale-data edge cases during refresh windows also complicate correctness guarantees.

### Persistent table with triggers

Rejected because it moves logic into database triggers, making the write path harder to test, debug, and version alongside application code. Trigger ordering and error handling become a maintenance burden.

### Application-level caching

Rejected for MVP because it adds cache invalidation logic before the performance need is demonstrated. The read-path cost of computed queries is acceptable at couple-scale transaction volumes and can be revisited if profiling shows a real bottleneck.
