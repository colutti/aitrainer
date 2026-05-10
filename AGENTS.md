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
make test-conversation    # Conversation flow e2e tests (10 scenarios)
make user-reset EMAIL=... # Reset user data for fresh test state
```

## Conversation Graph Nodes

The conversation graph (`backend/src/services/graph/conversation_graph.py`) runs these nodes per turn in fixed sequential order (all specialists run every turn, self-suppressing with no-op when they have nothing to contribute):

| Node | Model | Role |
|---|---|---|
| `session_context` | `qwen/qwen3-next-80b-a3b-instruct` | Hydrates turn context and recovers cross-turn `conversation_state` from history. LLM is used only for history sanitization. |
| `prompt_security` | `google/gemini-2.5-flash-lite` | Detects prompt injection and abuse (NOT product scoping). If blocked, short-circuits to blocked response. |
| `training_specialist` | `google/gemini-3.1-flash-lite-preview` | Domain specialist for training, workout logging, and exercise routine management. Emits `no_action_needed` when the turn is not about training. |
| `nutrition_specialist` | `google/gemini-3.1-flash-lite-preview` | Domain specialist for nutrition logging, adherence analysis, and metabolism parameter adjustments. Emits `no_action_needed` when the turn is not about nutrition. |
| `plan_specialist` | `openai/gpt-oss-120b` | Domain specialist for plan discovery, creation, review, and materialization readiness. Emits `no_action_needed` when the turn does not involve the plan. Uses `provider_sort: "throughput"`. |
| `coach_reply` | `google/gemini-3.1-flash-lite-preview` | **Pure synthesizer** — no tools. Synthesizes specialist outputs into a single coach-voiced response. Ignores no-op specialists. |
| `memory_hub` | `google/gemini-3.1-flash-lite-preview` | **Residual persistence** — stores durable facts and reminders. Must NOT create events as substitutes for domain operations. |

### Cross-turn conversation state

After each turn, a compact `[GRAPH_STATE_V1]` snapshot is persisted as a SYSTEM message in chat history (`backend/src/services/graph/conversation_contract.py`). This snapshot tracks `active_domain`, `pending_action` (resolved by priority from specialist suggestions), and `last_action_status`. On the next turn, `session_context` recovers it and injects it into `conversation_state`, which specialists can read via `context_blocks` for continuity. Old snapshots containing `primary_owner` and `interaction_mode` parse correctly (backward compatible).

### Sequential pipeline model

- All specialist nodes run every turn in fixed order after `prompt_security` passes.
- Each specialist decides internally whether to act or emit `no_action_needed`.
- There is no routing node, no `primary_owner`, no `interaction_mode`, no `secondary_nodes`, and no `handoff_target`.
- Pending actions are resolved by deterministic priority: `domain_execution` > `plan_discovery` > `plan_review` > `domain_analysis` > `none`.
- `pending_action` is consolidated between `plan_specialist` and `coach_reply`, before `memory_hub`.
- `active_domain` is derived from actual specialist contributions after each turn.
- On blocked turns, execution stops after `prompt_security`; `coach_reply` and `memory_hub` do not run.
- `coach_reply` has zero tools and zero operational authority.
- `memory_hub` cannot convert domain actions into calendar events.

### Persona isolation

Specialist nodes (training, nutrition, plan) operate in `persona_mode: "none"` and receive `history_summary_neutral` instead of raw `history_summary`. The `session_context` node uses an LLM to strip persona mannerisms (ex: "meu parceiro!", "sensacional!") while preserving all factual content. This prevents specialist nodes from adopting coach voice.

### Plan creation flow

The `plan_specialist` follows a 5-item discovery checklist (no explicit consent required):

1. Objetivo principal (ex: ganhar massa, perder gordura)
2. Prazo/meta (date or approximate deadline)
3. Disponibilidade semanal (days + minutes per session) - combines info across turns
4. Restrições/limitações ("nenhuma" is accepted)
5. Metabolismo (via `get_metabolism_data` tool)

When all 5 items are present, the plan_specialist calls `get_metabolism_data` → `plan_help` → `upsert_plan` in sequence.

### OpenRouter provider routing

The `plan_specialist` uses `provider_sort: "throughput"` in its node config to route to the fastest OpenRouter provider instead of the cheapest. This significantly reduced plan_specialist latency (~50%+). All other nodes use the default price-based routing which is optimal for flash-lite models.

Each node config JSON can set:
- `top_p` / `frequency_penalty` — LLM sampling params (default: null = use defaults)
- `provider_sort` — OpenRouter routing: "throughput", "latency", or "price" (default: null = price-based)

### Conversation E2E tests

Independent conversation flow tests live in `tests/conversation/`. Each file is self-contained (no shared imports, no dependency on backend `src/` modules) and tests one conversation scenario against the live backend:

```bash
cd backend && .venv/bin/pytest tests/conversation/ -v   # all 10 scenarios
cd backend && .venv/bin/pytest tests/conversation/test_01_verao_espanha.py -v  # single
make test-conversation  # shortcut
```

Prerequisites: backend running (`make dev`), user `rafacolucci@gmail.com` exists.

### User reset script

`backend/scripts/reset_user_data.py` resets all user data (plan, memories, events, chat history, message counters) while preserving login. Used by the conversation tests to start from clean state:

```bash
make user-reset EMAIL=rafacolucci@gmail.com
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
Keep project documentation updated whenever behavior, architecture, prompts, models, workflows, contracts, or operational guidance change.
