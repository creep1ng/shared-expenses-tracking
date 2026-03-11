# Product Glossary

## Account

A financial container that holds or represents money movement.

Examples:

- cash
- bank account
- savings account
- credit card account

Accounts are the real source or destination of transactions.

## Archived account

An account that is no longer actively selectable for new transactions but remains visible for historical records and reporting.

## Category

A classification for a financial movement.

Examples:

- groceries
- rent
- salary
- transportation

Categories help organize reporting and analytics.

## Archived category

A category that can no longer be used for new entries by default, but remains attached to historical transactions.

## Transaction

A recorded financial movement affecting one or more accounts within a workspace ledger.

Core transaction examples:

- income
- expense
- transfer

Transactions are the fundamental unit of the financial ledger.

In the current model, a transaction can reference a source account, a destination account, or both depending on its type.

## Transfer

A special type of transaction representing movement of money between two accounts.

Transfers are first-class ledger movements and must not be counted as normal income or expense in analytics.

## Workspace

The top-level context that owns financial data.

All accounts, categories, transactions, and reports belong to a workspace.

## Personal workspace

A workspace with a single member, used to manage finances alone.

## Shared workspace

A workspace with multiple members, used to manage finances collaboratively, such as with a partner.

## Workspace member

A user who belongs to a workspace and has a role governing access.

## Owner

A workspace member with elevated control, especially for settings and invitations.

## Member

A regular workspace participant with access to shared data according to permission rules.

## Split

The rule defining how the burden of a shared expense is divided between workspace members.

Examples:

- equal split
- custom percentage split
- one person paid but both share cost

## Split configuration

The stored data structure that explains how a shared expense should be allocated among participants.

## Paid by user

The workspace member who actually paid the money for a transaction.

This may differ from who ultimately bears the cost.

## Net balance

The resulting debt or credit position between members after considering shared transactions and split rules.

Typical example:

- one member paid more than their fair share, so the other member owes them money

## Settle up

A user action that records or reflects a reimbursement intended to reduce or clear a net balance between members.

## KPI

Key Performance Indicator. A high-level metric displayed on the dashboard.

Planned KPI examples:

- total balance
- total income
- total expenses
- net cash flow

## Ledger

The ordered financial record of accounts, transactions, and resulting balances.

The ledger is the source of truth for all analysis and reporting.

## Minor units

The smallest persisted unit of money for a currency.

Examples:

- cents for USD
- centavos for many Latin American currencies

Money should be stored in integer minor units rather than floating-point values.

## Acceptance Criteria

The concrete list of expected outcomes defined in a GitHub issue.

An issue is not complete unless its acceptance criteria are satisfied.

## Definition of Done

The shared quality and completion standard applied to every issue in this repository.

It includes functionality, code quality, tests, bug expectations, and documentation updates.
