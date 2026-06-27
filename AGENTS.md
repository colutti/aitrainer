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
- AI: Pydantic AI, OpenRouter, Mem0
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

## AI Chat Runtime

The conversation runtime is a single Pydantic AI agent call per user turn.
There are no graph nodes, routing nodes, specialist turns, or second internal
coach-rewrite call in the application code. Pydantic AI may still perform
multiple provider requests internally when tools are needed.

Key files:
- `backend/src/services/trainer.py`: API/Telegram facade and billing/history helpers.
- `backend/src/services/ai_chat/runner.py`: one-turn orchestration, SSE, persistence, and run logging.
- `backend/src/services/ai_chat/agent.py`: Pydantic AI `Agent` construction.
- `backend/src/services/ai_chat/model_factory.py`: OpenRouter model settings.
- `backend/src/services/ai_chat/prompts.py`: system instructions and current-turn prompt assembly.
- `backend/src/services/ai_chat/plan_execution.py`: deterministic explicit-approval detection for plan tools.
- `backend/src/services/ai_chat/tools/registry.py`: domain AI tool surface and dynamic toolset selection.
- `backend/src/services/ai_chat/validation.py`: fail-closed output/tool-result validation.
- `backend/src/services/ai_chat/models.py`: typed contracts for tool results, final output, and run logs.

### One-Turn Flow

1. `AITrainerBrain.send_message_ai()` delegates to `ChatTurnRunner.stream_turn()`.
2. The runner loads profile, trainer profile, plan/metabolism/agenda context, recent public history, and recent Pydantic AI message history.
3. If the current message is explicit approval for a recent plan creation/update, the runner injects `runtime_context.plan_execution.required_tool`.
4. The runner selects the smallest safe Pydantic AI toolsets for the turn.
5. The runner calls `agent.run(...)` once with `message_history`, `deps`, `conversation_id`, metadata, and selected `toolsets`.
6. Pydantic AI handles tool calls inside that run.
7. The final output must validate as `CoachTurnOutput`.
8. `validate_turn_output()` blocks false success claims when required tools did not save data, material changes did not happen, or external sync failed.
9. Successful turns persist the user/trainer pair in one MongoDB batch and log a redacted `ChatRunLog`.

### Tool Contract

All AI tools return `ToolResult` with:
- `tool_name`
- `status`
- `saved`
- `material_change`
- `message_for_ai`
- optional `payload`, `validation_errors`, `changed_resources`, and `external_sync_failed`

The LLM must not claim a mutation succeeded unless the relevant tool returned
`saved=true`. It must not claim a plan/training/nutrition material change unless
the relevant tool returned `material_change=true`.

The model sees domain tools, not every low-level operation. Core turns expose
`plan_ops`, `training_ops`, `nutrition_ops`, `body_ops`, `schedule_ops`,
`memory_ops`, `metabolism_ops`, and `profile_ops`. `hevy_ops` is selected only
for Hevy-specific turns. `raw_data_ops` is selected only for explicit technical
audit/debug/export/raw-data requests.

Each domain tool accepts an `action` or `domain` parameter plus typed arguments.
Legacy factory modules remain importable through `compat_tools.SimpleTool`, but
the AI runtime does not depend on external agent-framework decorators.

Correctable tool argument/semantic validation failures should use Pydantic AI
`ModelRetry`. Missing action-specific parameters should be rejected before any
mutation. Prompt logs must store result previews only; full raw tool payloads,
secrets, vectors, base64 content, and large document bodies must not be persisted
in `prompt_logs`.

### Plan Creation Flow

The agent follows a 5-item discovery checklist:

1. Objetivo principal (ex: ganhar massa, perder gordura)
2. Prazo/meta (date or approximate deadline)
3. Disponibilidade semanal (days + minutes per session)
4. Restrições/limitações ("nenhuma" is accepted)
5. Metabolismo via `get_metabolism_data`

When all 5 items are present, the agent should call:
1. `plan_ops(action="get_status")`
2. `metabolism_ops(action="get_data")`
3. `plan_ops(action="help")` when it needs the exact payload contract
4. `plan_ops(action="create_from_discovery")` only with a complete, typed payload

For existing plans, the agent should read with `plan_ops(action="get_status")`
or `plan_ops(action="get_plan")`, then mutate only through typed plan actions
such as `update_section` or `record_review`.

### OpenRouter Routing

The chat agent uses `OPENROUTER_CHAT_MODEL` with Pydantic AI
`OpenRouterModelSettings`. Defaults are optimized for latency and clarity:
`provider_sort="throughput"`, `parallel_tool_calls=false`, `reasoning.effort=low`,
and `reasoning.exclude=true`.

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
- `DB_NAME=aitrainer`
- `API_SERVER_PORT=8000`
- `QDRANT_PORT=6333`
- `MONGO_URI=mongodb://localhost:27017`
- `SECRET_KEY` (required)
- `LLM_STREAM_TIMEOUT_SECONDS=120`
- `LOG_LEVEL=INFO`
- `RATE_LIMIT_LOGIN=5/minute`
- `OPENROUTER_API_KEY` (required for AI chat and embeddings)
- `OPENROUTER_BASE_URL=https://openrouter.ai/api/v1`
- `OPENROUTER_CHAT_MODEL=google/gemini-3.5-flash`
- `OPENROUTER_SERVICE_TIER=priority`
- `OPENROUTER_EMBED_MODEL=openai/text-embedding-3-small`
- `OPENROUTER_EMBED_DIMENSIONS=768`

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
