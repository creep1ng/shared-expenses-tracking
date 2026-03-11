# Product Vision

## Purpose

Shared expenses tracking is intended to help users manage both personal finances and shared finances with a partner through a single workspace-oriented model.

The application should make it easy to record movements, understand where money is going, and reason about shared spending without fragmenting the experience into separate tools.

## Primary users

### Individual user

A person who wants to:

- register income and expenses
- organize finances by accounts and categories
- view balance and cash-flow indicators
- understand personal financial patterns over time

### Couple or partner-based users

Two people who want to:

- maintain a shared financial workspace
- register shared expenses clearly
- identify who paid and how the expense should be split
- understand net balances between them
- avoid ambiguity about reimbursements and settlements

## Core product promise

The product should provide a trustworthy financial ledger that supports:

- real accounts as sources and destinations of money
- explicit transaction modeling
- structured categories
- optional receipt evidence linked to a transaction record
- clean reporting boundaries for income, expenses, and transfers
- shared-expense logic built into the same ledger model

## Differentiator

The main product differentiator is not generic expense logging by itself. The differentiator is the combination of:

- personal and shared workspaces in one model
- accurate transaction tracking against accounts
- partner-oriented split logic
- visibility into net balances and settlement needs

## Product principles

### Workspace-first model

All financial data lives in a workspace context.

- a personal workspace is a workspace with one member
- a shared workspace is a workspace with multiple members

This keeps the model consistent and reduces future branching complexity.

### Ledger before analytics

Analytics are only trustworthy if the underlying ledger is consistent.

For that reason, the product should first ensure correctness in:

- account balances
- transaction linkage
- transfer behavior
- shared split behavior

Only then should richer charts, forecasts, and planning features be layered on top.

### Explicit over implicit

Financial behavior should be explicit in the data model and UI.

Examples:

- transfers are not normal expenses
- split rules should be visible and intentional
- ownership and access must be enforced by workspace membership

### Auditability and trust

The application should prioritize clear domain behavior over hidden automation.

Users should be able to understand:

- what happened
- which account was affected
- which category was assigned
- who paid
- how the cost burden was split
- why a balance or net debt changed

## Success criteria for the MVP

The MVP is successful if a user can:

- sign up and sign in securely
- create a personal or shared workspace
- create accounts and categories
- record transactions and transfers correctly
- see updated balances and basic KPIs
- register a shared expense and understand who owes whom

## Constraints

- The system must be designed for future growth but implemented incrementally.
- The project should support local development and deployment with Docker and Docker Compose.
- The project must use GitHub Flow and issue-driven implementation.
- Documentation, ADRs, and Mermaid diagrams are first-class artifacts.

## Non-goals for the initial release

The following are not required for the first usable version:

- complex itemized split transactions
- rich budget forecasting
- scheduled payment automation
- advanced debt tracking beyond partner net balance
- elaborate dashboard charts

Those features remain valid roadmap candidates, but they should not compromise the delivery of a reliable core ledger and shared-expense workflow.
