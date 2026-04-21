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
- Main frontend: React 19, TypeScript 5.9.3, Vite 7.2.4, TailwindCSS v4, Zustand 5, React Router 7.6, React Query, i18next 25.8, react-i18next 16.5
- Admin frontend: React 19, TypeScript 5.9.3, Vite 7.2.4, TailwindCSS v4
- AI: LangChain, LangGraph, Mem0
- AI providers: Gemini, OpenAI, Ollama
- Auth: Firebase
- Payments: Stripe
- Containers: Podman + `podman-compose`
- Containerized test dependencies: MongoDB, Qdrant, Stripe mock
- Testing: Pytest, Vitest 3.0.5, Playwright 1.50.2

## Development Rules

- Prefer TDD for changes; for bug fixes, start with a failing automated test.
- Keep lint and type checks clean. Treat warnings as work to fix, not to suppress.
- Do not assume old docs are accurate; validate against the repository before acting.
- When a command exists in the `Makefile`, prefer using it rather than inventing an alternative.
- The official full test path is containerized. Prefer `make test-once` over host-local mixed execution.
- `make verify` is the fast verification gate; `make verify-all` adds e2e; `make test-once` is the documented full-suite entrypoint.
- Playwright E2E must run through the containerized stack via `make e2e`, `make verify-all`, or `make test-once`. Do not treat host-local `npx playwright test` as the supported validation path.
- Any new or changed user-facing text must be translated for all app locales (`pt-BR`, `en-US`, `es-ES`) in the same task; do not ship partial localization.

## Validation Gates

- Any task that touches `frontend/` is incomplete until `cd frontend && npm run lint && npm run typecheck` passes after the last code edit.
- Any task that touches `frontend/admin/` is incomplete until `cd frontend/admin && npm run lint && npm run typecheck` passes after the last code edit.
- Any task that touches `backend/` is incomplete until `cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src` passes after the last code edit.
- Any task that touches `backend-admin/` is incomplete until `cd backend-admin && .venv/bin/pylint src && .venv/bin/pyright src` passes after the last code edit.
- Treat ESLint, Ruff, and Pylint warnings in touched files as failures to fix, not as acceptable cleanup for later.
- Do not stop at passing tests for frontend work. Lint and typecheck are required before claiming completion.
- Do not stop at passing tests for backend work. Ruff and Pylint are required before claiming completion.
- When a change affects multiple surfaces, run the validation gate for each affected surface.

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

`npx playwright test` above is for local experimentation only. The supported validation path for E2E is the containerized `make e2e` / `make verify-all` / `make test-once` flow.

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
make verify
make verify-all
make test-once
make e2e
make test-backend-cov
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
- `/plan`
- `/stats`
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
- `MONGO_URI=mongodb://localhost:27017`
- `SECRET_KEY` (required)
- `LLM_TEMPERATURE=0.4`
- `LOG_LEVEL=INFO`
- `RATE_LIMIT_LOGIN=5/minute`
- `GEMINI_LLM_MODEL=gemini-1.5-flash`
- `GEMINI_EMBEDDER_MODEL=gemini-embedding-001`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_LLM_MODEL=llama3-groq-tool-use:8b`
- `OLLAMA_EMBEDDER_MODEL=nomic-embed-text:latest`
- `OPENAI_API_KEY` (required for OpenAI provider)

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

## Task Completion Output

- Sempre que uma tarefa for finalizada, gerar um conjunto de test cases para a funcionalidade entregue.
- Antes de encerrar, automatizar todos os test cases que forem tecnicamente automatizáveis (unit, integration, e2e quando aplicável ao escopo).
- Expandir a cobertura de testes da funcionalidade com cenários além do fluxo feliz, incluindo falhas, condições não ideais, regressões, casos de borda e contorno.
- Na resposta final ao usuário, **não** listar todos os test cases: retornar apenas os casos que **não puderam ser automatizados** e que precisam de validação manual.
- Os casos manuais retornados devem ser apresentados em tabela com colunas `ID`, `Cenário`, `Passos`, `Resultado Esperado` e `Status`.
- O conjunto final (automatizado + manual residual) deve cobrir a tarefa em nível aceitável de qualidade.

## Maintenance

Keep this document updated when stack, commands, app boundaries, or validation workflow change.
