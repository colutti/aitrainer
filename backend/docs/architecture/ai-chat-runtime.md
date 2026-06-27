# AI Chat Runtime

## Summary

FityQ chat uses Pydantic AI as the only agent runtime. The backend makes one
application-level `Agent.run(...)` call per user turn. Pydantic AI may make
additional provider calls internally to execute tools, but the application no
longer runs a separate graph, specialist pipeline, or second coach-rewrite turn.

## Responsibilities

- `src/services/trainer.py`: public facade used by API and Telegram. Handles
  history access, message limits, SSE formatting, and memory helpers.
- `src/services/ai_chat/runner.py`: turn orchestration. Loads context/history,
  invokes the agent, validates the result, persists messages, and logs the run.
- `src/services/ai_chat/agent.py`: builds the Pydantic AI `Agent`.
- `src/services/ai_chat/model_factory.py`: central OpenRouter model settings.
- `src/services/ai_chat/prompts.py`: system instructions and current-turn prompt.
- `src/services/ai_chat/plan_execution.py`: deterministic same-turn approval
  detection for plan creation/update tools.
- `src/services/ai_chat/tools/registry.py`: domain tool surface, dynamic
  toolset selection, and legacy adapters compacting large outputs.
- `src/services/ai_chat/tools/base.py`: shared tool audit, timing, sanitized args,
  and error conversion.
- `src/services/ai_chat/validation.py`: fail-closed checks for false success
  claims.
- `src/repositories/chat_repository.py`: public chat history and Pydantic AI
  message-history conversion.

## Tool Contract

The model sees a small set of domain tools instead of every low-level operation.
Ordinary turns expose only core tools such as `plan_ops`, `training_ops`,
`nutrition_ops`, `body_ops`, `schedule_ops`, `memory_ops`, `metabolism_ops`,
and `profile_ops`. Hevy and raw-data tools are selected only for turns with
explicit Hevy or technical audit intent.

Each domain tool accepts an `action` or `domain` field plus typed arguments. For
example, active-plan edits use `plan_ops(action="update_section", ...)`; recent
nutrition reads use `nutrition_ops(action="get_recent", ...)`; raw technical
inspection uses `raw_data_ops(domain="workouts", ...)`.

All agent tools return `ToolResult`:

```json
{
  "tool_name": "update_plan_section",
  "status": "success",
  "saved": true,
  "material_change": true,
  "message_for_ai": "Plano atualizado com sucesso.",
  "changed_resources": ["plan"],
  "payload": {"plan_id": "..."}
}
```

Rules:

- Read tools use `saved=false` and `material_change=false`.
- Write tools use `saved=true` only after the underlying repository/API call
  succeeds.
- Plan/training/nutrition mutations use `material_change=true` only when user
  strategy or tracked data materially changed.
- External sync failures set `external_sync_failed=true` and must block success
  claims.
- Tool args logged in `ToolAuditEntry` are sanitized for secrets and large data.
- Tool result payloads are not persisted verbatim in prompt logs. Logs store a
  compact result preview with status, persistence flags, changed resources,
  error type, and payload shape.
- Correctable validation failures should raise Pydantic AI `ModelRetry` so the
  model can fix arguments inside the same `Agent.run(...)`.
- Missing action-specific parameters should raise `ModelRetry`; internal
  failures should return `ToolResult(status="error", saved=false)`.

## Explicit Plan Approval

The runtime keeps the "OK, pode aplicar" flow deterministic:

1. The runner loads recent public history before the agent call.
2. `plan_execution.detect_plan_execution_requirement()` checks whether the
   current message is explicit approval for a recent plan creation/update.
3. When detected, `runtime_context.plan_execution.required_tool` is injected.
4. `validate_turn_output()` blocks the final response if the required tool was
   not called or did not persist the requested change.

This preserves the one application-level agent call while preventing textual
reconfirmation loops.

## Performance Choices

- One application-level agent call replaces the previous multi-stage pipeline.
- Dynamic Pydantic AI toolsets keep the model-visible tool surface small. The
  backend selects the toolsets before `Agent.run(...)`; the model then chooses
  actions only from the selected domain tools.
- OpenRouter routing uses `provider_sort="throughput"` for the chat model.
- `parallel_tool_calls=false` keeps mutation ordering deterministic and easier
  to audit.
- Legacy raw-data tool outputs are compacted before reaching the model to avoid
  context bloat.
- Context loading is best-effort for optional blocks so one failed analytics
  query does not break chat.
- User/trainer messages persist in one MongoDB batch after successful turns.

## Logging and Observability

`ChatRunLog` is persisted through `database.log_prompt()`. It captures:

- status and error type
- requested model and service tier
- duration, context load time, and agent run time
- provider usage when available
- tool call count and ordered tool names
- selected toolsets, available model-visible tool names, and available tool
  count for the turn
- sanitized per-tool args, duration, result preview, and error type
- message size and history count

Provider-credit errors from OpenRouter are treated as external runtime failures:
the SSE stream returns a safe error and the failed reply is not persisted.

## Tests

Core coverage:

- `tests/unit/services/test_ai_chat_validation.py`
- `tests/unit/services/test_ai_chat_tools.py`
- `tests/unit/services/test_ai_chat_runner.py`
- `tests/unit/services/test_trainer_tools_raw.py`
- `tests/unit/services/test_trainer.py`
- `tests/unit/repositories/test_chat_repository.py`
- `tests/test_trainer_plan_prompt.py`

Before claiming backend completion, run:

```bash
cd backend
.venv/bin/pytest tests/unit/services/test_ai_chat_validation.py tests/unit/services/test_ai_chat_tools.py tests/unit/services/test_ai_chat_runner.py tests/unit/services/test_trainer_tools_raw.py -q
.venv/bin/ruff check src tests
.venv/bin/pylint src
```
