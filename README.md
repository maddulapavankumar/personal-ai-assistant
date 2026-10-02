# Personal AI Assistant (Incremental, Cost-Conscious)

This project is a production-minded **personal AI assistant** built incrementally, with strict scope control and low local cost.

## Current approach

We are intentionally starting small:

- FastAPI backend
- Local SQLite database
- Simple frontend later
- Memory + reminders as the first core features
- No voice/smart-home/distributed infra in v1

## Prerequisites (Windows)

Required:

- Git
- Python 3.11+
- Node.js 18+ (Node 16 works short-term, but upgrade recommended)

Optional for containerized local development:

- Docker Desktop

## Quick start (local)

```powershell
cd C:\Users\pa1ku\source\repos\personal-ai-assistant

# 1) Python virtual env
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip

# 2) Verify machine prerequisites
powershell -ExecutionPolicy Bypass -File .\scripts\check-prereqs.ps1
```

## Environment setup

Copy and edit `.env.example` when app code is scaffolded:

```powershell
Copy-Item .env.example .env
```

Fill `OPENAI_API_KEY` only when you are ready to run LLM features.

## Backend (current scaffold)

Install backend dependencies:

```powershell
cd C:\Users\pa1ku\source\repos\personal-ai-assistant\backend
python -m pip install -r requirements.txt
```

Run the API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:

```powershell
pytest -q
```

Control extraction per chat request (optional):

- `extraction_mode = "auto"` (default behavior, runs deterministic extraction)
- `extraction_mode = "off"` (skips extraction for that request)

Memory quality controls:

- duplicate extracted memories are deterministically suppressed (same user + type + normalized content)
- `GET /api/v1/memories?status=ACTIVE|SUPERSEDED|REJECTED|PENDING_REVIEW` can filter by status
- `GET /api/v1/memories/{memory_id}` returns one memory by id for the current user
- `GET /api/v1/memories/review-queue` supports optional filtering/sorting (`status`, `type`, `sort_by`, `order`)
- low-confidence extracted memories are stored as `PENDING_REVIEW` for explicit approval/rejection
- status transition guardrails are enforced (`PENDING_REVIEW -> ACTIVE|REJECTED`, `ACTIVE -> SUPERSEDED|REJECTED`, `SUPERSEDED -> ACTIVE|REJECTED`, `REJECTED` terminal)
- chat responses can include deterministic `memory_context` with up to 3 matching ACTIVE memories

Deterministic chat reminder command:

- `remind me to <title> at <ISO-8601 datetime>`
- `update reminder <id> title <text> at <ISO-8601 datetime>`
- `cancel reminder <id>`
- `show reminders`
- `show reminders due today` (local server time)
- `show reminders due this week` (local server time)
- `brief me`
- `show daily briefing`
- `what changed since yesterday`
- `show daily delta`
- Example: `remind me to pay rent at 2026-10-05T09:00:00Z`
- Example: `update reminder 12 title pay internet bill at 2026-10-06T08:30:00Z`
- Example: `cancel reminder 12`
- reminder audit events are appended for create/update/cancel with deterministic status (`executed`, `ignored`, `invalid`)

Routine suggestions v1:

- `GET /api/v1/routines/suggestions` returns deterministic, read-only routine suggestions from ACTIVE memories + ACTIVE reminders
- stable ordering by confidence (desc) then title (asc)

Daily briefing v1:

- `GET /api/v1/briefings/daily` returns deterministic, read-only daily briefing data
- includes reminders due today (local server date), top 3 ACTIVE memories, and routine suggestions
- top memories are sorted by importance (desc), confidence (desc), updated_at (desc), then id (asc)
- `GET /api/v1/briefings/daily-delta` returns deterministic day-over-day counts (today vs yesterday), including due reminder delta and new item counts

## Recommended milestone flow (Copilot Agents)

Use a strict 3-role flow per milestone:

1. Planner agent
2. Builder agent
3. Reviewer agent

Detailed prompts and guardrails are in:

- [docs/agent-workflow.md](./docs/agent-workflow.md)
- [docs/github-review-setup.md](./docs/github-review-setup.md)

## GitHub quality gates

This repository includes:

- CI workflow: [.github/workflows/backend-ci.yml](./.github/workflows/backend-ci.yml)
- PR template: [.github/pull_request_template.md](./.github/pull_request_template.md)
- Code owners: [.github/CODEOWNERS](./.github/CODEOWNERS)
- Process guards workflow: [.github/workflows/repo-process-guards.yml](./.github/workflows/repo-process-guards.yml)
  - `pr-template-compliance` (required/failing)
  - `definition-of-done-gate` (required/failing)
    - backend code/tests require `README.md` updates
    - workflow/scripts require process-doc updates (`docs/github-review-setup.md`, `docs/agent-workflow.md`, `.github/instructions/agent-scope-control.instructions.md`)
  - `docs-instructions-drift` (warning-only)

After pushing, configure branch protection for `main` per:

- [docs/github-review-setup.md](./docs/github-review-setup.md)

## Current repository status

- Milestone 1 Step 2 (deterministic extraction): merged to `main` via PR #1.
- Milestone 1 Step 3 (tool routing controls): merged to `main` via PR #2.
- Milestone 1 Step 4 (memory quality controls): merged to `main` via PR #3.
- Milestone 1 Step 5 (chat reminder command): merged to `main` via PR #4.
- Milestone 1 Step 6 (repo process automation): merged to `main` via PR #5.
- Milestone 1 Step 7 (memory review queue workflow): merged to `main` via PR #6.
- Milestone 1 Step 8 (memory inspection quality controls): merged to `main` via PR #7.
- Milestone 1 Step 9 (deterministic reminder update/cancel lifecycle): merged to `main` via PR #8.
- Milestone 1 Step 10 (deterministic smoke journey): merged to `main` via PR #9.
- Milestone 2A Step 11 (definition-of-done docs mapping gate): merged to `main` via PR #10.
- Milestone 2B Step 12 (memory-aware chat context): merged to `main` via PR #11.
- Milestone 2B Step 13 (reminder query commands): merged to `main` via PR #12.
- Milestone 2B Step 14 (routine suggestions v1): merged to `main` via PR #13.
- Milestone 2C Step 15 (daily briefing endpoint): merged to `main` via PR #14.

Recommended immediate sequence:

1. Keep the next slice small and testable.
2. Start the next milestone branch from updated `main`.
3. Start the next slice with Planner -> Builder -> Reviewer flow.

## First implementation milestone (approved target)

Build only:

- chat API skeleton with deterministic rule-based memory extraction
- memory model + CRUD endpoints
- reminder model + CRUD endpoints
- basic routine-candidate table + read endpoint
- tests for changed behavior

Do not build yet:

- voice
- smart-home control
- autonomous external side effects
- heavy infra/microservices
