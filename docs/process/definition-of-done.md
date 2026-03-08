# Definition of Done

The following Definition of Done applies to all issues in this repository.

- [ ] Functionality: All the elements of the issue's Acceptance Criteria must be completed.
- [ ] Code: The code works, it runs locally and it's integrated on the goal branch without breaking the system.
- [ ] Quality: The code passes the linter, type checks and automated validations.
- [ ] Testing coverage: There are tests according to the change and all the required tests passes the CI validation.
- [ ] Bugs: There aren't critical bugs associated with the implementation.
- [ ] Docs: There were updated the technical documentation, README, API contracts, diagrams or use notes if the implementation requires it.

## Interpretation guidance

### Functionality

Acceptance criteria are mandatory, not aspirational.

If the issue defines user-visible or technical requirements, they must be implemented or the issue remains incomplete.

### Code

The implementation must:

- run locally
- fit the approved architecture
- avoid breaking adjacent workflows
- integrate cleanly with the target branch

### Quality

Quality includes:

- formatting
- linting
- type checking
- schema and validation consistency

### Testing coverage

Tests should be proportional to the risk and scope of the change.

High-risk financial logic must not rely only on manual validation.

### Bugs

An issue is not done if it introduces known critical defects into the primary flow.

### Docs

Update documentation whenever implementation affects:

- product behavior
- setup or usage
- API contracts
- architecture or data model
- runtime flows
- contributor expectations

## Additional repository rule

If a feature changes architecture, data schema, permissions, API behavior, or core runtime flow, the corresponding docs and Mermaid diagrams must be updated in the same branch.
