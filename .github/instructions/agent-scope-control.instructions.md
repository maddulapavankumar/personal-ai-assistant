---
description: Enforce strict milestone scope control for all implementation tasks in this repository.
---

# Agent Scope Control

All coding work must follow a milestone contract before implementation starts.

## Required contract fields

- Goal
- Non-goals
- Files to create/modify
- Validation commands
- Stop conditions

## Execution rules

1. Implement only approved scope.
2. Do not add dependencies without approval.
3. Do not expand API/schema scope without approval.
4. If requirements are ambiguous, stop and ask.
5. Run targeted tests for changed behavior before handoff.
6. Before milestone handoff, refresh directly related process docs (README status, workflow/checklist docs, and instruction learnings when applicable).

## Learnings

- Multi-agent work in this repository must use explicit Planner -> Builder -> Reviewer phases per milestone; parallel builders on one milestone caused drift risk and should be avoided.
- Scope expansion should be treated as a blocker requiring explicit user confirmation, not as an opportunity for proactive additions.
- Keep milestones small and testable (one vertical slice at a time) to preserve predictable Copilot-generated output quality.
- For stacked milestone pull requests, use previous step branch as PR base first, then retarget to `main` after prior step merges to preserve small, reviewable diffs.
- PR template placeholders must be replaced with concrete evidence before merge; incomplete template text is treated as a process failure.
