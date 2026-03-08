# Definition of Ready

An issue is ready for implementation when the problem and expected outcome are clear enough that a contributor can execute the work without inventing essential product behavior.

## Required conditions

- [ ] The issue explains the user or business problem.
- [ ] The issue contains explicit Acceptance Criteria or Definition of Done items specific to the feature.
- [ ] Dependencies on other issues or architectural work are identified.
- [ ] The impacted domain areas are identified, such as auth, workspace, accounts, categories, transactions, split logic, dashboard, or docs.
- [ ] Expected backend and frontend impact is known, if applicable.
- [ ] The issue indicates whether data model, API, or permission changes are expected.
- [ ] The documentation impact is considered.
- [ ] It is clear whether an ADR is required.

## Recommended issue structure

Each implementation issue should ideally include:

- problem statement
- user story or developer need
- acceptance criteria
- non-goals or exclusions
- dependencies
- testing notes
- documentation notes
- ADR needed: yes or no

## Questions to answer before implementation

### Product clarity

- What user behavior is being enabled or improved?
- What is explicitly in scope?
- What is explicitly out of scope?

### Domain impact

- Which entities or workflows are affected?
- Does the issue alter account balance behavior?
- Does it alter split or net balance logic?
- Does it alter permissions?

### Technical impact

- Are migrations expected?
- Are new endpoints expected?
- Are new background tasks expected?
- Does the issue introduce a new dependency or cross-cutting pattern?

### Documentation impact

- Should the README change?
- Should product scope docs change?
- Should architecture diagrams change?
- Should an ADR be added?

## Not ready examples

An issue is not ready if it:

- describes a vague idea without acceptance criteria
- combines several unrelated features without boundaries
- depends on unresolved architecture choices
- requires hidden assumptions about data or permissions
- omits critical workflow behavior for financial correctness

## Rule for contributors

If an issue is not ready, refine the issue or related docs before implementing the feature.

Do not silently fill major product gaps with guesswork when the issue lacks sufficient definition.
