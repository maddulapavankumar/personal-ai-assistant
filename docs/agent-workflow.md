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

## Product intent and non-negotiables

This repository is intentionally constrained. Every AI agent should follow the same intent as the human owner:

- Ship small, vertical slices instead of broad platform features.
- Favor deterministic, low-cost behavior over speculative or overbuilt AI orchestration.
- Keep the feature set focused on personal assistant workflows: memory, reminders, daily briefings, routine suggestions, and lightweight UI.
- Do not add framework, dependency, service, or schema changes without explicit approval.
- Do not “fix” unrelated code while working on a milestone; stay within the approved files and behavior.
- If a requirement is ambiguous, stop and ask before changing code or architecture.
- Treat repository process, docs, and review gates as part of the product, not as optional overhead.

The agent’s job is not to invent a better product; the job is to advance the approved slice while preserving the existing workflow and guardrails.

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

## GitHub CLI quickstart for agents

Use the CLI for this repo's normal PR flow so the process is easy for any agent to follow:

```powershell
cd C:\Users\pa1ku\source\repos\personal-ai-assistant
powershell -ExecutionPolicy Bypass -File .\scripts\ensure-gh-path.ps1
gh auth status

gh pr create --base main --head <branch-name> --title "<milestone title>" --body-file .github\pull_request_template.md
gh pr checks
gh pr view --comments
gh pr merge <number> --squash --delete-branch
```

Use `gh` instead of manual browser PR creation whenever feasible. This reduces tool drift and makes the milestone workflow explicit and reusable for AI agents.

## PR and handoff checklist

Before requesting merge:

1. Ensure PR template fields are fully filled (no placeholder comments left).
2. Include exact validation commands and outcomes (pass/fail).
3. Resolve all selected review comments and re-run targeted tests.
4. Confirm CI checks are green.
5. Confirm `pr-template-compliance` check is green.

When using stacked milestone branches:

- Create `step-(n+1)` from `step-n` branch.
- Open PR with base = `step-n` and compare = `step-(n+1)` to keep diff focused.
- After `step-n` merges, retarget `step-(n+1)` PR to `main`.

## Definition of done for each milestone

Before closing a milestone, ensure:

1. README status section reflects latest merged/open milestone state.
2. Instruction learnings are updated when a reusable pattern/pitfall was discovered.
3. PR body includes final test outcomes after any follow-up fixes.
4. If process docs changed, include them in the same milestone PR unless scope requires a separate docs PR.

## Repo automation guardrails

This repo includes process automation in:

- [.github/workflows/repo-process-guards.yml](../.github/workflows/repo-process-guards.yml)

Guard behavior:
- `pr-template-compliance` fails PRs with incomplete template/checklist evidence.
- `definition-of-done-gate` fails PRs when backend/workflow changes do not include required documentation updates per changed-file mapping rules.
- `docs-instructions-drift` warns (does not fail) when code changes lack aligned process-doc updates.
