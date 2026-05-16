# Graph Runtime

The conversation graph runs one fixed sequential pipeline:

1. `session_context`
2. `prompt_security`
3. `training_specialist`
4. `nutrition_specialist`
5. `plan_specialist`
6. `coach_reply`
7. `memory_hub`

All specialists run every safe turn and self-suppress with `no_action_needed` when they have no contribution.

## Specialist Contract

Analytical nodes return strict JSON with separate public and internal channels:

```json
{
  "action_status": "executed | failed | needs_user_input | no_action_needed",
  "public_message": "user-facing message or empty string",
  "internal_analysis": "technical peer-only analysis",
  "operation_result": {
    "attempted": false,
    "succeeded": false,
    "tool_name": "",
    "error_code": "",
    "evidence": ""
  }
}
```

Rules:

- No-op: `public_message=""`, `internal_analysis=""`, `operation_result.attempted=false`.
- Needs input: `public_message` asks only the next blocking question, and only for a fact genuinely external to the system.
- Successful tool action: `action_status=executed`, `operation_result.succeeded=true`.
- Failed tool action: `action_status=failed`, `operation_result.succeeded=false`, and `public_message` says the action was not completed.
- Internal technical content flows through `internal_analysis`, not through the user-facing channel.

Specialists are technical authorities by default. They must decide domain-owned parameters from context, history, active plan, and tools whenever possible. Asking the user is an exception, not a neutral fallback.

Valid user questions are limited to external facts the system cannot infer, such as a new injury, equipment limitation, preference, deadline, or availability change. Invalid user questions include specialist-owned technical parameters such as training sets, rep ranges, load guidance, or nutrition macro targets when the system already has enough context to decide.

The runtime records each normalized specialist result in `GraphState.specialist_results` and appends non-empty public messages to `GraphState.coach_handoff`.

## Coach Contract

`coach_reply` has no tools and no operational authority. It receives `coach_handoff` plus persona context. It does not receive raw `training_analysis`, `nutrition_analysis`, `active_plan`, or `metabolism` as factual inputs.

The coach may rewrite tone and transitions only. It cannot add facts, numbers, recommendations, plan status, tool outcomes, or success claims. Failed operations must remain failed.

## Memory Contract

`memory_hub` reads `specialist_results` and `persistence_candidates`, not coach prose. `coach_response` and `coach_reply` are not factual sources for persistence.

If any material operation has `operation_result.attempted=true` and `operation_result.succeeded=false`, the runtime blocks memory, event, and summary writes for the turn.

## Plan Rules

`plan_specialist` uses `openai/gpt-oss-120b`, `temperature: 0.1`, `reasoning: low`, `provider_sort: throughput`, `parallel_tool_calls: false`, and plan-only tools.

For plan work:

- Single-domain training update requires material `training_analysis`; nutrition no-op is acceptable.
- Single-domain nutrition update requires material `nutrition_analysis`; training no-op is acceptable.
- Full plan creation requires material training and nutrition analyses.
- `plan_specialist` must not normalize specialist-owned technical indecision into legitimate user discovery.
- `public_message` may say a plan was created, saved, or updated only when `operation_result.succeeded=true` for `upsert_plan`.
- `ERRO_UPSERT_PLAN_*` forces `plan_status=update_failed`, `action_status=failed`, and `pending_action.kind=plan_review`.

## Model Matrix

| Node | Model | Temperature | Tools | Context |
|---|---:|---:|---|---|
| `session_context` | `qwen/qwen3-next-80b-a3b-instruct` | `0.0` | none | neutral history sanitation |
| `prompt_security` | `google/gemini-2.5-flash-lite` | `0.0` | none | request only |
| `training_specialist` | `google/gemini-3-flash-preview` | `0.2` | training/Hevy only | no trainer persona |
| `nutrition_specialist` | `google/gemini-3-flash-preview` | `0.2` | nutrition only | no trainer persona |
| `plan_specialist` | `openai/gpt-oss-120b` | `0.1` | plan only | training/nutrition analysis |
| `coach_reply` | `google/gemini-3.1-flash-lite-preview` | `0.2` | none | `coach_handoff` and persona |
| `memory_hub` | `google/gemini-3.1-flash-lite-preview` | `0.0` | orchestrator-only | specialist results, candidates |

## Debug Trace

Graph debug traces include:

- top-level `specialist_results`
- top-level `coach_handoff`
- per-node `specialist_result`
- state snapshots containing `specialist_results` and `coach_handoff`

These fields are the source of truth for verifying whether a tool action was attempted, succeeded, failed, or withheld from the coach and memory layers.
