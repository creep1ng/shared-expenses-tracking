# Product Scope

## Scope strategy

The issue tracker contains a broad product roadmap. This document defines what belongs in the MVP, what belongs immediately after the MVP, and what should remain out of scope until the financial core is stable.

## MVP scope

The MVP must establish a reliable financial foundation before adding advanced planning or analytics.

### Included capabilities

#### 1. Authentication and sessions

- user registration
- sign in and sign out
- secure session persistence
- protected route behavior
- password reset flow if practical within the bootstrap window

Primary issue:

- `#26 Authentication and Session Management`

#### 2. Workspace onboarding

- create a personal workspace
- create a shared workspace
- invite a partner into a shared workspace
- identify current workspace context in the UI

Primary issue:

- `#27 Workspace and Personal Space Onboarding`

#### 3. Roles and permissions

- owner and member roles
- owner control over workspace settings and invitations
- backend enforcement of protected actions

Primary issue:

- `#35 Workspace Roles and Permissions`

#### 4. Accounts CRUD

- create, view, edit, archive accounts
- support cash, bank, savings, and credit card account types
- maintain current balance semantics

Primary issue:

- `#28 Accounts CRUD Foundation`

#### 5. Categories CRUD

- create, edit, archive categories
- preserve historical visibility of archived categories
- prevent invalid duplicate use within the selected scope

Primary issue:

- `#29 Categories CRUD Foundation`

#### 6. Transactions CRUD

- create, view, edit, and delete transactions
- enforce account and category linkage
- recalculate affected balances correctly

Primary issues:

- `#30 Transactions CRUD Foundation`
- `#23 Link Transactions to Accounts and Categories`

#### 7. Transfers

- register transfers between accounts
- validate source and destination differences
- exclude transfers from expense and income analytics

Primary issue:

- `#31 Transfers Between Accounts`

#### 8. Base dashboard KPIs

- total balance
- total income for period
- total expenses for period
- net cash flow for period

Primary issue:

- `#33 Dashboard Base KPI Cards`

#### 9. Shared-expense split MVP

- record who paid a transaction
- support equal or custom split rules for partner-oriented expenses
- calculate net balance within a shared workspace
- provide a simple settle-up flow later in MVP if feasible

Primary issues:

- reduced slice of `#5 Database Schema Migration for Split Logic`
- reduced slice of `#20 Partner Split Toggle for Transactions`

## Near-term post-MVP scope

These items are important, but they should follow the financial core and shared-expense MVP.

### History and filtering

- `#32 Transaction History, Filters and Search`

### Settings and preferences

- `#34 Settings and Preferences`

### Faster transaction entry UX

- `#21 Frictionless Transaction Data Entry UX`

### Advanced transaction metadata

- `#24 Advanced Transaction Metadata Options`

### Credit card account refinements

- `#1 Decremental sum for credit cards`
- `#13 Credit Card Available Limit Display`

### Read-only dashboard enhancements

- `#6 Current Balance Trend Line Chart`
- `#7 Expenses per Category Bar Chart in Dashboard`
- `#8 Expenses vs Earnings Comparison Line Chart`

## Explicitly deferred beyond MVP

The following are valid roadmap items but should be deferred until the core system is stable and tested.

### Receipts and file management

- `#22 Integrate Receipt Uploads into Transaction Form`

### Budgets and forecasts

- `#3 Budgeting module`
- `#15 Budgeting Module with Progress Visuals`
- `#19 Inline Budget Progress Visualization`
- `#2 Expenses forecast`
- `#14 Spending Trajectory Forecast Against Budget Limit`

### Scheduled payments

- `#18 Scheduled Subscriptions Warning`
- `#25 Scheduled Payments Management`

### Debt tracking beyond partner net balance

- `#12 Localized Informal Debt Logging`

### Savings goals and advanced card/debt analytics

- `#10 Credit Card Debt Area Chart with Cut-off Marker`
- `#11 Savings and Goals KPI Indicators on Dashboard`

### Advanced split and segmentation workflows

- `#17 Split Transaction into Multiple Segments`

## Delivery sequence

Recommended order:

1. `#36` environment bootstrap and CI/CD
2. `#26` authentication and sessions
3. reduced `#5` schema foundation for workspace and split-ready transactions
4. `#27` workspace onboarding
5. `#35` roles and permissions
6. `#28` accounts CRUD
7. `#29` categories CRUD
8. `#30` + `#23` transactions CRUD and linkage
9. `#31` transfers
10. `#33` dashboard KPIs
11. reduced `#20` shared split and net balance
12. `#32` and `#34` for usability and consistency

## Product boundary rules

When deciding whether a new request belongs in MVP, use these checks:

- Does it strengthen ledger correctness?
- Does it strengthen the personal/shared workspace experience?
- Does it improve trust in balances and shared expense outcomes?
- Can it be built without introducing major architectural complexity too early?

If the answer is mostly no, it likely belongs after the MVP.
