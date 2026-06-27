# Prompt Context Service

The AI chat runtime uses one Pydantic AI agent call per user turn. Dynamic
context is built by `backend/src/services/ai_chat/context.py` and injected into
the current user prompt by `backend/src/services/ai_chat/prompts.py`.

`PromptBuilder` remains only as a local compatibility helper for older tests and
non-runtime callers. It is not the production chat path.

## Runtime Contract

`build_runtime_context()` returns a JSON-serializable dict with contract version
`prompt_context_v1`.

Top-level shape:

```json
{
  "contract_version": "prompt_context_v1",
  "session": {
    "current_date": "YYYY-MM-DD",
    "current_time": "HH:MM",
    "day_of_week": "Saturday",
    "user_timezone": "Europe/Madrid",
    "channel": "app | telegram"
  },
  "trainer": {
    "name": "atlas",
    "trainer_type": "atlas",
    "preferred_language": "pt-BR",
    "profile": "..."
  },
  "user": {
    "email": "user@example.com",
    "name": "Aluno",
    "profile": "..."
  },
  "agenda": {
    "events": []
  },
  "metabolism": {},
  "plan": {
    "summary": "formatted active plan or discovery context",
    "status": "ACTIVE_PLAN | DISCOVERY_IN_PROGRESS | NO_PLAN",
    "has_active_plan": true,
    "discovery": {}
  },
  "plan_execution": {
    "explicit_user_approval": true,
    "mode": "update_active_plan",
    "required_tool": "update_plan_section",
    "must_execute_now": true
  }
}
```

## Message Assembly

The production call is:

1. `ChatTurnRunner.stream_turn()` loads context and recent public history.
2. `build_user_prompt(user_input, runtime_context)` creates the single current
   prompt sent to Pydantic AI.
3. `Agent.run(...)` receives that prompt, `message_history`, `deps`,
   `conversation_id`, metadata, and the selected Pydantic AI toolsets.
4. Pydantic AI handles any internal tool-call requests.
5. The final model output must validate as `CoachTurnOutput`.

## Tool Safety

The model sees domain tools such as `plan_ops`, `training_ops`,
`nutrition_ops`, `body_ops`, `schedule_ops`, `memory_ops`, `metabolism_ops`,
and `profile_ops`. `hevy_ops` and `raw_data_ops` are selected only for matching
turn intent. Each domain tool accepts a typed `action` or `domain`.

Every AI-facing tool returns `ToolResult`. The final response validator blocks:

- required-tool turns where the required tool was not called successfully
- `operation_status="saved"` without a successful saved tool
- `material_change=true` without a successful material tool result
- failed external syncs, especially Hevy plan/routine synchronization

Tools must keep docstrings explicit about when to use them, whether they mutate
state, and what proof the model needs before claiming success.

`plan_execution.required_tool` uses internal legacy operation names such as
`update_plan_section` for deterministic validation. The model should satisfy
that requirement through the matching domain action, for example
`plan_ops(action="update_section")`.

Correctable argument or semantic validation failures should use Pydantic AI
`ModelRetry` so the model can repair the tool call in the same run.

## Logging

Each turn writes a `ChatRunLog` through `database.log_prompt()`. It includes
duration, model settings, selected toolsets, available model-visible tool names,
token usage when provider metadata is available, tool count, tool names,
sanitized args, per-tool duration, status, error type, and a compact result
preview. Full raw tool payloads must not be persisted in prompt logs.
