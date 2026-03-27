# AGENTS.md

## Overview

FityQ is an AI personal trainer platform with:
- Main app: `frontend/` + `backend/`
- Admin app: `frontend/admin/` + `backend-admin/`
- Infra and shared commands in [Makefile](/home/colutti/projects/personal/Makefile)

Source of truth for project operations is the codebase, especially:
- [README.md](/home/colutti/projects/personal/README.md)
- [Makefile](/home/colutti/projects/personal/Makefile)
- [frontend/package.json](/home/colutti/projects/personal/frontend/package.json)
- [frontend/admin/package.json](/home/colutti/projects/personal/frontend/admin/package.json)
- [backend/src/core/config.py](/home/colutti/projects/personal/backend/src/core/config.py)

## Current Stack

- Backend: FastAPI, Python 3.12, MongoDB, Qdrant
- Main frontend: React 19, TypeScript, Vite 7, TailwindCSS v4, Zustand, React Router 7, React Query
- Admin frontend: React 19, TypeScript, Vite 7, TailwindCSS v4
- AI: LangChain, LangGraph, Mem0
- AI providers: Gemini, OpenAI, Ollama
- Auth: Firebase
- Payments: Stripe
- Containers: Podman + `podman-compose`
- Containerized test dependencies: MongoDB, Qdrant, Stripe mock
- Testing: Pytest, Vitest, Playwright

## Development Rules

- Prefer TDD for changes; for bug fixes, start with a failing automated test.
- Keep lint and type checks clean. Treat warnings as work to fix, not to suppress.
- Do not assume old docs are accurate; validate against the repository before acting.
- When a command exists in the `Makefile`, prefer using it rather than inventing an alternative.
- The official full test path is containerized. Prefer `make test-once` over host-local mixed execution.

## Core Commands

### Full stack

```bash
make up
make down
make build
make build-prod
make restart
make debug-rebuild
make debug-rebuild-admin
```

### Main backend

```bash
cd backend
.venv/bin/python src/api/main.py
.venv/bin/ruff check src
.venv/bin/pylint src
.venv/bin/pyright src
.venv/bin/pytest
```

### Admin backend

```bash
cd backend-admin
.venv/bin/python src/main.py
.venv/bin/pylint src
.venv/bin/pyright src
```

### Main frontend

```bash
cd frontend
npm run dev
npm run build
npm run lint
npm run typecheck
npm run check
npm test
npx playwright test
```

### Admin frontend

```bash
cd frontend/admin
npm run dev
npm run build
npm run lint
npm run typecheck
npm run check
npm test
```

### Useful project targets

```bash
make test-once
make ci-fast
make ci-test
make security-check
make user-list
make user-get EMAIL=user@example.com
make user-nuke EMAIL=user@example.com
make invite-create EMAIL=user@example.com
make admin-promote EMAIL=user@example.com
```

## Architecture Notes

### Main backend

- App entrypoint: [backend/src/api/main.py](/home/colutti/projects/personal/backend/src/api/main.py)
- Configuration: [backend/src/core/config.py](/home/colutti/projects/personal/backend/src/core/config.py)
- API endpoints live in [backend/src/api/endpoints](/home/colutti/projects/personal/backend/src/api/endpoints)
- Business logic lives in [backend/src/services](/home/colutti/projects/personal/backend/src/services)
- Data access lives in [backend/src/repositories](/home/colutti/projects/personal/backend/src/repositories)
- Trainer personas live in [backend/src/trainers](/home/colutti/projects/personal/backend/src/trainers)

Current routed areas include:
- `/user`
- `/message`
- `/trainer`
- `/memory`
- `/workout`
- `/nutrition`
- `/weight`
- `/metabolism`
- `/dashboard`
- `/integrations/hevy`
- `/onboarding`
- `/telegram`
- `/stripe`

### Admin backend

- App entrypoint: [backend-admin/src/main.py](/home/colutti/projects/personal/backend-admin/src/main.py)
- Admin routes include:
  - `/admin/analytics`
  - `/admin/users`
  - `/admin/prompts`
  - `/admin/tokens`

### Frontend structure

- Main app features live in [frontend/src/features](/home/colutti/projects/personal/frontend/src/features)
- Shared code lives under `frontend/src/shared`
- Admin app lives in [frontend/admin/src](/home/colutti/projects/personal/frontend/admin/src)

## Environment Notes

Important backend settings currently defined in code:
- `AI_PROVIDER=gemini` by default
- Gemini, OpenAI and Ollama are supported
- `EMBEDDING_MODEL_DIMS=768`
- `DB_NAME=aitrainer`
- `API_SERVER_PORT=8000`
- `QDRANT_PORT=6333`

Do not hardcode environment assumptions that are not present in [backend/src/core/config.py](/home/colutti/projects/personal/backend/src/core/config.py) or the local env files.

## Agent Workflows

Project-specific workflows live in [`.agent/workflows`](/home/colutti/projects/personal/.agent/workflows):
- `brainstorming.md`
- `writing-plans.md`
- `executing-plans.md`
- `report-bug.md`
- `run-all-tests.md`
- `cleancode.md`

These files are guidance, not executable commands. If they drift from the repository, fix the workflow doc first or follow the codebase as source of truth.

Project-specific design skill:
- [`.agent/skills/ui-ux-pro-max/SKILL.md`](/home/colutti/projects/personal/.agent/skills/ui-ux-pro-max/SKILL.md)

## Maintenance

Keep this document updated when stack, commands, app boundaries, or validation workflow change.
