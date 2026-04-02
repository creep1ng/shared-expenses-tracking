# shared-expenses-tracking

Shared expenses tracking is a workspace-based personal finance application focused on two complementary use cases:

- managing personal finances in a structured way
- managing shared expenses with a partner, including split logic and settlement visibility

## Getting started

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.13 (for local backend development)

### Setup

1. Copy `.env.example` to `.env`.
2. Replace placeholder values such as `<db-user>` and `<db-password>` with local development credentials.
3. Run the full stack:

```bash
make up
```

### Common commands

- `make dev` — run frontend and backend locally with hot reload
- `make up` — run the full Docker Compose topology in the background
- `make down` — stop all containers
- `make migrate` — run database migrations
- `make lint` — run linters
- `make format` — run formatters
- `make typecheck` — run type checks
- `make test` — run all tests
- `make ci` — run lint, typecheck, and test

## Documentation

- [AGENTS.md](AGENTS.md): operating instructions for agentic contributors and implementation rules
- [docs/product/vision.md](docs/product/vision.md): product goals, target users, and constraints
- [docs/product/scope.md](docs/product/scope.md): MVP and post-MVP scope boundaries
- [docs/product/glossary.md](docs/product/glossary.md): shared business vocabulary
- [docs/process/development-workflow.md](docs/process/development-workflow.md): GitHub Flow and delivery process
- [docs/process/definition-of-ready.md](docs/process/definition-of-ready.md): issue readiness expectations
- [docs/process/definition-of-done.md](docs/process/definition-of-done.md): shared definition of done
- [docs/process/documentation-standards.md](docs/process/documentation-standards.md): documentation rules and expectations
- [docs/adr/](docs/adr/): architecture decision records
- [docs/architecture/system-overview.md](docs/architecture/system-overview.md): system and container architecture
- [docs/architecture/data-model.md](docs/architecture/data-model.md): data model and schema relationships
- [docs/architecture/runtime-flows.md](docs/architecture/runtime-flows.md): request and workflow interactions
