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

After pushing, configure branch protection for `main` per:

- [docs/github-review-setup.md](./docs/github-review-setup.md)

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
