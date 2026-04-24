# Prompt Context Service (OpenRouter Preset)

This backend uses an OpenRouter preset (`OPENROUTER_CHAT_MODEL`) as the source of
system instructions. The local backend no longer builds a large instruction prompt.

## Runtime Contract

`PromptBuilder.build_input_data()` generates `runtime_context` and
`runtime_context_json` with contract version `prompt_context_v1`.

Top-level shape:

```json
{
  "contract_version": "prompt_context_v1",
  "session": {
    "current_date": "YYYY-MM-DD",
    "current_time": "HH:MM",
    "day_of_week": "Segunda-feira",
    "user_timezone": "Europe/Madrid",
    "channel": "app | telegram"
  },
  "trainer": {
    "name": "Atlas",
    "profile": "trainer profile summary"
  },
  "user": {
    "name": "Aluno",
    "profile": "user profile summary"
  },
  "agenda": {
    "events_summary": "formatted agenda text"
  },
  "metabolism": {
    "summary": "formatted metabolism text"
  },
  "plan": {
    "summary": "formatted active plan text",
    "has_active_plan": true
  }
}
```

## Message Assembly

`PromptBuilder.get_prompt_template()` now creates:

1. `system`: minimal payload wrapper
2. `chat_history`: `MessagesPlaceholder`
3. `human`: current user message

System content format:

```text
RUNTIME_CONTEXT_JSON (PROMPT_CONTEXT_V1):
{runtime_context_json}
```

## Configuration and Safety

- `OPENROUTER_CHAT_MODEL` must start with `@preset/` (validated in settings).
- `PROMPT_CONTEXT_CONTRACT_VERSION` defaults to `prompt_context_v1`.
- If preset configuration is invalid, app startup fails via settings validation.

## Preset Authoring Guidance

OpenRouter preset instructions should:

- Treat `RUNTIME_CONTEXT_JSON` as primary dynamic context.
- Prefer `plan.summary` and `plan.has_active_plan` for plan behavior.
- Respect `session.channel` for response formatting differences.
- Avoid requiring extra placeholders not present in the contract.
