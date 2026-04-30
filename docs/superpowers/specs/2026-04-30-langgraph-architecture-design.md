# LangGraph Runtime Architecture (Execution Spec)

## Goal

Replace the single-agent orchestration with an explicit graph runtime that keeps shared context stable, enforces prompt safety, guarantees persistence checks, and makes node-level prompt/model changes easy through repository files.

## Node Topology (9 nodes)

1. `TurnContextNode`
2. `PromptSecurityNode`
3. `IntentRouterNode`
4. `PlanManagerNode`
5. `TrainingSpecialistNode`
6. `NutritionSpecialistNode`
7. `GeneralConversationNode`
8. `PersistenceGuardNode`
9. `PersonaResponseNode`

## Runtime State Contract

- `request`: raw and sanitized input, user/channel metadata, correlation ids
- `shared_context`: profile, trainer profile, agenda, metabolism, active plan, runtime context
- `security`: security verdict and blocked flags
- `routing`: detected intent and routing decisions
- `training_analysis`: structured training payload
- `nutrition_analysis`: structured nutrition payload
- `plan_workspace`: plan brief, conflicts, final plan candidate
- `persistence_intents`: memory/event actions and execution status
- `response`: technical response and final persona response
- `ops`: node config hash, tool calls, node outcomes, trace metadata

Implementation note:
- the runtime now exposes these sections explicitly in `GraphState`, while still keeping convenience top-level fields for execution ergonomics.

## Prompt/Model Configuration

Prompt and model selection are file-backed per node in:

- `backend/src/services/agents/config/nodes/*.json`
- `backend/src/services/agents/config/prompts/*.md`
- `backend/src/services/agents/config/README.md` (editing and validation workflow)

`AgentConfigRegistry` is the runtime loader and validator.

Implementation contract:
- Prompt markdown files are the full system prompts per node.
- Runtime does not inject behavioral objective text; it injects only:
  - `AVAILABLE_CONTEXT` from manifest `context_blocks`
  - `PEER_INPUTS` from manifest `peer_inputs`
  - `OUTPUT_CONTRACT` from manifest `output_contract`
- Trainer persona context is restricted to `persona_response` (`persona_mode=final_only`).
- Node-level model assignments in manifests are runtime defaults.

## Observability Policy

- LangSmith tracing is the primary execution trace.
- Every graph execution has one root run and one child run per node.
- Logs must include correlation ids and node names.
- Node config hash/version must be attached to trace metadata.
- Prompt security decisions and persistence decisions must be auditable.

## Safety Policy

`PromptSecurityNode` runs before intent routing. If the message is unsafe, content is blocked or sanitized before any domain node executes.

## Persistence Policy

`PersistenceGuardNode` runs before final response, decides and executes memory/event actions (`create`, `update`, `delete`) with deduplication checks.

Implementation note:
- persistence now follows `planner -> executor`: the node first produces structured persistence intents via LLM, then executes the approved event/memory action in deterministic code.

## Coordination Policy

- Specialists always receive the same shared runtime context payload.
- `NutritionSpecialistNode` also receives `TrainingSpecialistNode` output when available.
- `TrainingSpecialistNode` receives `NutritionSpecialistNode` output on revision pass.
- `PlanManagerNode` evaluates consistency after specialist outputs and can trigger one revision cycle.

## Dev Test Setup

No containers are auto-started by this spec rollout. To test manually:

1. Graph is enabled by default. To force legacy fallback for debugging:
   - `ENABLE_EXPERIMENTAL_CONVERSATION_GRAPH=false`
2. Start stack when you are ready:
   - `make dev`
3. Validate APIs:
   - Main backend: `http://localhost:8000/health`
   - Admin backend: `http://localhost:8001/health`
4. Inspect node configs:
   - `GET /admin/agent-configs`
   - `GET /admin/agent-configs/{node_name}`
