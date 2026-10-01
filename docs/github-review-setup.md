# GitHub Review Setup (Recommended)

This repository uses strict milestone scope control with Planner -> Builder -> Reviewer phases. Complete the following GitHub settings once to enforce it.

## 1) Protect `main`

In GitHub:

`Settings -> Branches -> Add branch protection rule`

Use:

- Branch name pattern: `main`
- Require a pull request before merging
- Require approvals: `1` minimum
- Dismiss stale approvals when new commits are pushed
- Require review from Code Owners
- Require conversation resolution before merging
- Require status checks to pass before merging
  - Required check: `backend-tests`
- Restrict force pushes

## 2) Keep PRs milestone-sized

PR template is enforced via:

- [pull_request_template.md](../.github/pull_request_template.md)

Every PR should include:

- Goal
- Non-goals
- Files changed
- Validation commands
- Stop-condition confirmation

## 3) Branch naming convention

Use:

- `milestone-<n>-step-<n>-<short-topic>`

Examples:

- `milestone-1-step-2-memory-extraction`
- `milestone-1-step-3-tool-routing`

## 4) Review discipline

For each PR:

1. Planner scope approved
2. Builder implementation done
3. Reviewer findings addressed
4. CI green
5. Merge

