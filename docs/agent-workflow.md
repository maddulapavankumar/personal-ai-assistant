# Copilot Agent Workflow (Scope-Controlled)

Use this workflow for **every milestone** to prevent drift.

## Roles

1. **Planner**
   - Defines exact scope, files, assumptions, non-goals, validation, and stop conditions.
2. **Builder**
   - Implements only approved scope.
   - Stops and asks if scope changes.
3. **Reviewer**
   - Checks correctness and scope adherence.
   - Flags risky deviations and missing tests.

## Milestone Contract Template

Before coding, planner must define:

- Goal
- Non-goals
- Files to create/modify
- API/data changes
- Validation commands
- Stop conditions

## Stop Conditions (mandatory)

Builder or reviewer must stop and ask before continuing if:

- A new dependency is needed
- Schema scope expands beyond approved milestone
- New API surface appears beyond plan
- Architecture changes significantly
- Requirement is ambiguous

## Prompt: Planner

```text
Act as senior software architect.
Create the plan for Milestone <N> only.
Output:
1) Goal
2) Non-goals
3) Assumptions
4) Files to create/modify
5) API/data changes
6) Validation plan
7) Risks
8) Stop conditions
Do not expand to future phases unless asked.
```

## Prompt: Builder

```text
Implement only the approved Milestone <N> scope.
Do not add new dependencies or architecture unless explicitly approved.
If requirements are ambiguous, stop and ask.
Add tests for changed behavior.
Return:
- files changed
- tests added/updated
- validation results
- open questions/blockers
```

## Prompt: Reviewer

```text
Review implementation against the approved Milestone <N> contract.
Report:
- scope deviations
- correctness issues
- missing tests
- architecture concerns
- security/privacy concerns
Rank findings by severity and confidence.
Do not broaden scope.
```

## Default milestone cadence

1. Planner output approved
2. Builder implementation
3. Reviewer findings
4. Fixes
5. Milestone sign-off

## PR and handoff checklist

Before requesting merge:

1. Ensure PR template fields are fully filled (no placeholder comments left).
2. Include exact validation commands and outcomes (pass/fail).
3. Resolve all selected review comments and re-run targeted tests.
4. Confirm CI checks are green.

When using stacked milestone branches:

- Create `step-(n+1)` from `step-n` branch.
- Open PR with base = `step-n` and compare = `step-(n+1)` to keep diff focused.
- After `step-n` merges, retarget `step-(n+1)` PR to `main`.
