# LangGraph Prompt, Context, and Model Refactor Implementation Plan (Revised)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

## Goal

Make prompt files the full source of truth for each graph node, enforce per-node context allowlists, concentrate trainer persona in the final synthesis node, and assign explicit OpenRouter models per node.

## Current Status Snapshot (2026-04-30)

- Node manifest schema with `context_blocks`, `peer_inputs`, `persona_mode`, `output_contract`: implemented.
- Admin inspection endpoint returning expanded schema: implemented.
- Prompt assembly using `AVAILABLE_CONTEXT`, `PEER_INPUTS`, `OUTPUT_CONTRACT`: implemented.
- Inline `OBJETIVO DO NO` removed from system prompt: implemented.
- Backend/backend-admin gates listed below: passing in latest run.
- Manual operational validation in dev/LangSmith: pending.

---

## Task 1: Contract and Config Integrity

**Files**
- `backend/src/services/agents/config_registry.py`
- `backend/tests/unit/services/test_agent_config_registry.py`
- `backend/src/services/agents/config/README.md`
- `backend-admin/src/api/endpoints/admin_agent_configs.py`

### Acceptance Criteria

- Registry validates and exposes:
  - `context_blocks: list[str]` (required)
  - `peer_inputs: list[str]` (optional, default `[]`)
  - `persona_mode: "none" | "final_only"`
  - `output_contract: str` (required)
- `config_hash` reflects the effective prompt + contract fields.
- `as_metadata()` includes context-policy fields.
- `/admin/agent-configs` returns expanded contract fields.

### Required Verification

- `cd backend && .venv/bin/pytest tests/unit/services/test_agent_config_registry.py -v`

---

## Task 2: Prompt Assembly and Context Policy

**Files**
- `backend/src/services/graph/conversation_graph.py`
- `backend/tests/unit/services/test_conversation_graph.py`

### Acceptance Criteria

- `_run_llm_node()` system prompt contains:
  - `AVAILABLE_CONTEXT`
  - `PEER_INPUTS`
  - `OUTPUT_CONTRACT`
- System prompt does **not** include inline `OBJETIVO DO NO`.
- Context resolution is per-node via allowlist:
  - `_build_context_catalog(state)`
  - `_resolve_node_context(cfg, state)`
  - `_resolve_peer_inputs(cfg, state)`
- `turn_context` persists canonical runtime blocks in `state.shared_context`.
- Trace/input metadata includes `context_blocks`, `peer_inputs`, `persona_mode`.
- Deterministic boundaries unchanged:
  - persistence guard execution path
  - tool allowlists
  - prompt-security pre-block behavior

### Required Verification

- `cd backend && .venv/bin/pytest tests/unit/services/test_conversation_graph.py -v`

---

## Task 3: Node Manifests and Prompt Files

**Files**
- `backend/src/services/agents/config/nodes/*.json`
- `backend/src/services/agents/config/prompts/*.md`
- `backend/tests/unit/services/test_agent_config_registry.py`

### Required Model Defaults

- `turn_context`: `openai/gpt-5-nano`
- `prompt_security`: `openai/gpt-5-nano`
- `intent_router`: `openai/gpt-5-nano`
- `training_specialist`: `openai/gpt-4.1-mini`
- `nutrition_specialist`: `openai/gpt-4.1-mini`
- `plan_specialist`: `openai/gpt-4.1-mini`
- `general_conversation`: `openai/gpt-4o-mini`
- `persistence_guard`: `openai/gpt-5-nano`

### Prompt Content Requirements

Each prompt file must define:
- role
- objective
- allowed context
- forbidden assumptions
- tool policy
- output contract
- quality bar

### Required Verification

- `cd backend && .venv/bin/pytest tests/unit/services/test_agent_config_registry.py -v`

---

## Task 4: Documentation and Full Validation

**Files**
- `docs/superpowers/specs/2026-04-30-langgraph-architecture-design.md`
- `backend/src/services/agents/config/README.md`
- `docs/superpowers/plans/2026-04-30-langgraph-prompt-context-model-refactor.md`

### Acceptance Criteria

- Architecture spec explicitly states:
  - prompt files are full prompts
  - context is node-scoped by allowlist
  - persona reaches only the final synthesis node
  - manifest models are runtime defaults
- Operator README documents manifest schema and runtime contract.

### Required Verification Gates

- `cd backend && .venv/bin/pytest tests/unit/services/test_agent_config_registry.py tests/unit/services/test_conversation_graph.py tests/unit/core/test_experimental_graph_flag.py`
- `cd backend && .venv/bin/ruff check src tests`
- `cd backend && .venv/bin/pylint src`
- `cd backend-admin && .venv/bin/pylint src`
- `cd backend-admin && .venv/bin/pyright src`

---

## Task 5: Manual Validation Protocol (Deterministic)

### M-01 Prompt Exposure by Node

1. Start backend in dev with LangSmith tracing enabled.
2. Send one message: `quero ajustar treino e dieta para essa semana`.
3. Inspect node runs (`graph.*`) and capture system prompts.
4. Validate:
   - `prompt_security` only receives request-oriented context.
   - `training_specialist` and `nutrition_specialist` do not receive `trainer_persona`.
   - `general_conversation` receives `trainer_persona`.

### M-02 Runtime Config Drift Check

1. Edit one node manifest model and one prompt file line.
2. Restart backend.
3. Call:
   - `GET /admin/agent-configs/{node}`
4. Validate response reflects:
   - `model_name`
   - `prompt_text`
   - `context_blocks`
   - `peer_inputs`
   - `persona_mode`
   - `output_contract`
   - `config_hash`

### M-03 Multi-Domain Flow

1. Send one multi-domain request (training + nutrition).
2. Validate node execution order and participation:
   - `training_specialist`
   - `nutrition_specialist`
   - `plan_specialist`
   - `general_conversation`
   - `persistence_guard`
3. Validate model names used match node manifests.

---

## Commit Strategy

Default strategy for this branch: **single consolidated commit** after all gates pass and manual checks are recorded.
If the partner requests granular history, split into per-task commits.

---

## Automated Coverage Targets

- registry validation rejects malformed contract fields
- admin endpoint exposes effective prompt/model/context metadata
- `prompt_security` receives only request context
- `general_conversation` alone receives `trainer_persona`
- `nutrition_specialist` can consume `training_analysis`
- prompt rendering includes `AVAILABLE_CONTEXT`, `PEER_INPUTS`, `OUTPUT_CONTRACT`
- inline objective text is absent from runtime system prompt
- node metadata/input carries policy fields and config hash

---

## Manual Residual Tracking Table

| ID | Cenário | Passos | Resultado Esperado | Status |
|---|---|---|---|---|
| M-01 | Inspeção real de prompts por nó | Executar protocolo M-01 | Persona só no `general_conversation`; contexto mínimo por nó | Pendente |
| M-02 | Verificação operacional de config | Executar protocolo M-02 | Endpoint reflete schema expandido + hash atualizado | Pendente |
| M-03 | Fluxo multi-domínio completo | Executar protocolo M-03 | Nós e modelos corretos conforme manifesto | Pendente |
