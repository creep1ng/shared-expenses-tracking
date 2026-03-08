# Data Model

## Data model intent

The initial schema must support:

- secure user access
- personal and shared workspaces
- workspace membership and permissions
- account-based financial tracking
- categorized transactions
- future-safe shared-expense splitting

## Core entities

### users

Represents an authenticated person using the system.

### sessions

Represents authenticated session state managed by the backend.

### workspaces

Represents the top-level financial context.

Workspace types:

- personal
- shared

### workspace_members

Joins users to workspaces and defines their role.

Initial roles:

- owner
- member

### workspace_invitations

Represents the invitation flow for joining a shared workspace.

### accounts

Represents financial sources and destinations for money movement.

Initial account types:

- cash
- bank account
- savings account
- credit card

### categories

Represents financial classifications for transactions.

Initial category kinds:

- income
- expense

### transactions

Represents financial movements.

Initial movement types:

- income
- expense
- transfer

For shared-expense support, transactions should be able to store:

- payer identity
- split configuration

## Key invariants

- every account belongs to a workspace
- every category belongs to a workspace or seed-derived scope strategy
- every transaction belongs to a workspace
- transaction permissions derive from workspace membership
- transfers must not count as standard income or expense in analytics
- money values are stored in integer minor units

## Initial ER diagram

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ WORKSPACE_MEMBERS : joins
    WORKSPACES ||--o{ WORKSPACE_MEMBERS : has
    WORKSPACES ||--o{ WORKSPACE_INVITATIONS : issues
    WORKSPACES ||--o{ ACCOUNTS : owns
    WORKSPACES ||--o{ CATEGORIES : owns
    WORKSPACES ||--o{ TRANSACTIONS : owns
    USERS ||--o{ TRANSACTIONS : pays
    ACCOUNTS ||--o{ TRANSACTIONS : affects
    CATEGORIES ||--o{ TRANSACTIONS : classifies

    USERS {
        uuid id
        string email
        string password_hash
        datetime created_at
        datetime updated_at
    }

    SESSIONS {
        uuid id
        uuid user_id
        string session_key
        datetime expires_at
        datetime created_at
    }

    WORKSPACES {
        uuid id
        string name
        string type
        datetime created_at
        datetime updated_at
    }

    WORKSPACE_MEMBERS {
        uuid id
        uuid workspace_id
        uuid user_id
        string role
        datetime joined_at
    }

    WORKSPACE_INVITATIONS {
        uuid id
        uuid workspace_id
        string email
        string status
        datetime expires_at
        datetime created_at
    }

    ACCOUNTS {
        uuid id
        uuid workspace_id
        string name
        string type
        string currency
        int balance_minor
        boolean archived
        datetime created_at
    }

    CATEGORIES {
        uuid id
        uuid workspace_id
        string name
        string type
        string icon
        string color
        boolean archived
        datetime created_at
    }

    TRANSACTIONS {
        uuid id
        uuid workspace_id
        uuid account_id
        uuid category_id
        uuid paid_by_user_id
        string type
        int amount_minor
        string currency
        json split_config
        datetime occurred_at
        string description
        datetime created_at
        datetime updated_at
    }
```

## Notes on future evolution

Likely future schema extensions include:

- credit card limit and cutoff metadata
- receipts and attachments
- richer transaction metadata
- scheduled payments
- budgets
- settlement-specific records or derived net balance views

Those additions should be layered onto the core model rather than forcing a redesign of workspace, accounts, categories, and transactions.
