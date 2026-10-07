# GitHub Review Setup (Recommended)

This repository uses strict milestone scope control with Planner -> Builder -> Reviewer phases. Complete the following GitHub settings once to enforce it.

## 0) Install and authenticate GitHub CLI

Use the GitHub CLI instead of browser-only PR flows whenever possible. This makes the workflow deterministic for agents and future automation.

### Install / repair PATH

```powershell
cd C:\Users\pa1ku\source\repos\personal-ai-assistant
powershell -ExecutionPolicy Bypass -File .\scripts\ensure-gh-path.ps1
```

### Authenticate

```powershell
gh auth login --web
```

### Sanity check

```powershell
gh auth status
gh --version
```

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
  - Required check: `pr-template-compliance`
  - Required check: `definition-of-done-gate`
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
- or the current repo convention: `feat/<milestone-slug>` for milestone branches

Examples:

- `milestone-1-step-2-memory-extraction`
- `milestone-1-step-3-tool-routing`
- `feat/m4-step27-memory-review-queue`

## 4) Standard PR lifecycle for agents

When a milestone is ready, follow this exact flow:

```powershell
# ensure gh is available in the session
powershell -ExecutionPolicy Bypass -File .\scripts\ensure-gh-path.ps1

# create/update the milestone branch from main
git checkout -b feat/m4-step27-memory-review-queue

# after implementation and validation
git add -A
git commit -m "frontend: restore memory review queue actions"
git push --set-upstream origin feat/m4-step27-memory-review-queue

# open PR using the repo template
gh pr create --base main --head feat/m4-step27-memory-review-queue --title "frontend: restore memory review queue actions" --body-file .github\pull_request_template.md

# inspect checks and review state
gh pr checks

gh pr view --comments

# merge once checks are green and the review gate is satisfied
gh pr merge feat/m4-step27-memory-review-queue --squash --delete-branch
```

Use `gh pr create` instead of browser-only PR creation whenever possible. This keeps the workflow consistent, scriptable, and easier for agents to follow.

## 5) Review discipline

For each PR:

1. Planner scope approved
2. Builder implementation done
3. Reviewer findings addressed
4. CI green
5. Merge

## 5a) Low-severity advisory policy for Copilot reviews

GitHub branch protection does not natively support "ignore low severity only". To keep the workflow aligned with your preference, use a helper script before merging:

```powershell
cd C:\Users\pa1ku\source\repos\personal-ai-assistant
powershell -ExecutionPolicy Bypass -File .\scripts\check-pr-review-policy.ps1 -PullRequest <number>
```

Behavior:

- `low` findings are advisory only and do not block merge.
- `medium`, `high`, and `critical` findings fail the script and block the PR merge.
- If the PR has no review findings, the script exits successfully.
- This should be used as a pre-merge gate, alongside CI and reviewer approval.

Example:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-pr-review-policy.ps1 -PullRequest 42
```

This gives a practical GitHub-native workflow when a repository owner wants to allow low-severity findings without permitting medium/high issues to slip through.

The same rule is also enforced in CI via [.github/workflows/repo-process-guards.yml](../.github/workflows/repo-process-guards.yml), which runs the same review-policy check automatically for every PR targeting `main`.

The local and CI scripts also normalize GitHub CLI PATH handling and make `-IncludeLow` explicitly opt into a stricter low-severity blocking mode. In the default repo policy, low findings remain advisory while medium/high/critical findings block the PR.

## 6) Repo process automation checks

Workflow: [repo-process-guards.yml](../.github/workflows/repo-process-guards.yml)

- `pr-template-compliance` (**required/failing**) checks PR body completeness against the milestone template.
- `definition-of-done-gate` (**required/failing**) enforces changed-files -> required-docs mapping for backend and workflow/script changes.
  - backend app/test changes require `README.md` updates in the same PR.
  - workflow/script changes require updates to:
    - `docs/github-review-setup.md`
    - `docs/agent-workflow.md`
    - `.github/instructions/agent-scope-control.instructions.md`
- `docs-instructions-drift` (**warning-only**) signals when code/workflow changes happen without corresponding README/workflow/instruction updates.
