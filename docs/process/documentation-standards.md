# Documentation Standards

## Documentation philosophy

This repository uses documentation as part of the implementation process.

Docs are expected to:

- clarify intent before code exists
- explain why decisions were made
- stay aligned with behavior as the project evolves
- help humans and coding agents work consistently

## Docs as code

- Store documentation in version control with the implementation.
- Update documentation in the same branch as the code when a change affects behavior or architecture.
- Prefer small, focused documentation changes over large delayed updates.

## Markdown conventions

- Use clear section headings.
- Prefer concise paragraphs and bullets over dense prose.
- Keep terminology consistent with `docs/product/glossary.md`.
- Use code fences for commands, directory trees, and configuration examples.

## Mermaid conventions

Mermaid is the default diagram format.

Use the most appropriate type:

- C4-style diagram for system boundaries and containers
- ER diagram for entity relationships and schema views
- sequence diagram for request and workflow interactions
- flowchart for business or process decisions

## Diagram update rules

Update diagrams when:

- a new container or service is introduced
- a major runtime interaction changes
- a data relationship changes
- a business process gains new branches or states

Keep diagrams close to the narrative that explains them.

## ADR conventions

Use ADRs for decisions that are hard to reverse or broadly impactful.

Each ADR should contain:

- title
- status
- date
- context
- decision
- consequences
- alternatives considered
- related issues or PRs when relevant

## Documentation locations

- `README.md`: repository and project overview
- `AGENTS.md`: contributor operating rules
- `docs/product/`: product intent, scope, terminology
- `docs/process/`: workflow, quality gates, standards
- `docs/adr/`: architecture decisions
- `docs/architecture/`: structure, data model, runtime flows

## Update matrix by change type

### Product capability change

Update:

- relevant feature or product docs
- scope docs if MVP boundaries change
- README if the project overview changes

### Data model or schema change

Update:

- architecture data model doc
- ER diagram
- API docs if contracts change
- ADR if the rule is architectural

### Architecture or deployment change

Update:

- system overview
- container diagram
- ADR
- README if setup or topology changes

### Runtime workflow change

Update:

- runtime flow docs
- sequence diagrams
- API docs if relevant

### Process or contributor rule change

Update:

- `AGENTS.md`
- process docs

## Quality rule

If documentation is impacted by a change and not updated, the work is incomplete.
