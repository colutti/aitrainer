# LangSmith Traceability Design

## Summary

Implement LangSmith tracing in the backend for operational debugging, with full prompt/response visibility, correlation by user/session, isolated environments, and fail-open behavior.

This integration is observability-only. It does not replace the current internal prompt log persistence and must not affect user-facing execution when LangSmith is unavailable.

## Goals

- Trace all backend LLM executions centrally.
- Correlate traces by user and current session identifier.
- Capture prompts, responses, tool activity, latency, model resolution, and usage metadata.
- Keep dev and prod fully isolated.
- Ensure tracing failures never break application behavior.

## Non-Goals

- LangSmith evals, datasets, or quality scoring.
- Frontend instrumentation.
- Replacing existing database prompt logs.
- Content redaction in this iteration.

## Current Context

The backend already centralizes LLM execution in [backend/src/services/llm_client.py](/home/colutti/projects/personal/backend/src/services/llm_client.py). That file is the common path for simple model calls and tool-enabled agent execution.

The trainer flow in [backend/src/services/trainer.py](/home/colutti/projects/personal/backend/src/services/trainer.py) already passes `user_email` and uses a `log_callback` for internal prompt logging. The backend also already captures operational metadata such as prompt hash, token counts, resolved model/provider, tool usage, duration, cost, and status.

This existing structure makes `LLMClient` the correct integration boundary for LangSmith.

## Recommended Approach

Use a hybrid integration:

- native LangSmith tracing from the LangChain execution layer
- a small internal helper layer to standardize metadata, tags, run naming, environment isolation, and fail-open behavior

This balances automatic nested tracing for models and tools with explicit business metadata required for production debugging.

## Architecture

### Integration Boundary

Create a focused module at `backend/src/core/langsmith.py`.

This module is responsible for:

- reading LangSmith-related settings
- deciding whether tracing is effectively enabled
- building tracing-aware `RunnableConfig`
- standardizing `run_name`, `tags`, and `metadata`
- encapsulating fail-open safeguards

`LLMClient` remains the only service that applies tracing during LLM execution.

### Why `LLMClient`

`LLMClient` already owns:

- provider binding
- simple streaming execution
- tool-enabled agent execution
- usage metadata extraction
- final operational logging

Instrumenting here gives global backend coverage without coupling endpoints or business services directly to LangSmith.

### Scope of Instrumentation

Tracing must be applied to:

- `stream_simple(...)`
- `stream_with_tools(...)`

Run names should be stable and operationally meaningful:

- `chat.simple`
- `chat.tools`

LangSmith should capture nested model and tool activity automatically through the LangChain execution path. The internal helper layer should only add the missing operational context.

### Boundary Rules

- `Trainer` should not import or call LangSmith directly.
- API endpoints should not know about tracing.
- Existing database prompt logs remain active and independent.

## Configuration

Add the following settings in [backend/src/core/config.py](/home/colutti/projects/personal/backend/src/core/config.py):

- `LANGSMITH_TRACING_ENABLED: bool = False`
- `LANGSMITH_API_KEY: str = ""`
- `LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"`
- `LANGSMITH_PROJECT: str = ""`
- `LANGSMITH_ENVIRONMENT: str = "local"`
- `LANGSMITH_SAMPLE_RATE: float = 1.0`

### Effective Enablement Rules

- If `LANGSMITH_TRACING_ENABLED=false`, the backend behaves exactly as it does today.
- If tracing is enabled but required configuration is missing, the backend logs a warning and continues without tracing.
- Invalid tracing configuration must never prevent application startup or request execution.

### Environment Isolation

Environment isolation is mandatory.

Recommended setup:

- dev project: `fityq-backend-dev`
- prod project: `fityq-backend-prod`

Requirements:

- separate LangSmith projects per environment
- separate credentials per environment
- explicit `LANGSMITH_ENVIRONMENT` value per environment
- environment tags on every run even when projects are already separated

The same API key must not be reused across dev and prod.

## Trace Contract

### Content Policy

For this iteration, traces include full payloads:

- prompts
- responses
- tool outputs available through the traced execution

This is intentional. The design assumes the team accepts the privacy and compliance implications for the selected environments.

The architecture must still preserve the ability to add future redaction without redesigning the integration boundary.

### Tags

Each traced run should include standardized tags:

- `env:dev|prod|local`
- `surface:backend`
- `flow:chat`
- `mode:simple|tools`
- `provider:openrouter|gemini|openai|ollama`

### Metadata

Each traced run should include, when available:

- `user_email`
- `session_id`
- `prompt_name`
- `prompt_hash`
- `prompt_chars`
- `messages_count`
- `tools_available`
- `tools_called`
- `requested_model`
- `resolved_model`
- `resolved_provider`
- `usage_cost`
- `service_tier`
- `duration_ms`
- `status`

### Session Correlation

The system currently relies heavily on `user_email` as the effective session identifier in chat flows.

Rule:

- use an explicit session identifier if one is available in the execution path
- otherwise fall back to the current effective identifier, which is `user_email`

This rule must be explicit in the implementation to avoid inconsistent trace correlation.

## Execution Flow

### `stream_simple(...)`

At the start of execution:

- compute tracing config through the new helper module
- attach stable run name, tags, and initial metadata

During and after execution:

- capture resolved model/provider metadata when available
- capture token and usage metadata already extracted by the service
- mark final status and duration

### `stream_with_tools(...)`

At the start of execution:

- compute tracing config through the new helper module
- attach stable run name, tags, and initial metadata

During and after execution:

- allow LangSmith to capture nested model and tool spans through LangChain
- append final `tools_called`
- append resolved model/provider metadata
- append duration, cost, and status

### Internal Logging Compatibility

The existing internal `log_callback` path remains unchanged in purpose.

LangSmith tracing and database logging run in parallel and must not depend on each other.

## Failure Handling

Tracing must be fail-open in all environments.

If LangSmith initialization or publishing fails:

- log a warning with minimal operational context
- continue request execution normally
- do not suppress or replace the real business/runtime error
- do not prevent tool execution
- do not block prompt logging to the internal database

This includes failures in:

- tracing initialization
- callback creation
- config assembly
- metadata attachment
- remote publishing

## Rollout Plan

### Phase 1: Dev Only

- enable tracing only in dev
- validate prompt/response visibility
- validate tool traces
- validate user/session correlation
- validate resolved model, cost, and duration metadata
- confirm streaming behavior remains stable

### Phase 2: Production Enablement

- enable tracing in prod with dedicated config
- start with `LANGSMITH_SAMPLE_RATE=1.0`
- monitor volume and operational usefulness

### Phase 3: Optional Enrichment

- store LangSmith identifiers such as `trace_id` or `run_id` alongside internal logs when available
- add direct cross-reference between internal support workflows and LangSmith traces

This third phase is intentionally out of scope for the initial delivery.

## Testing Strategy

### Unit Tests for Tracing Helper

Add tests covering:

- config generation when tracing is enabled
- no-op behavior when tracing is disabled
- graceful fallback when required credentials/config are missing
- standardized tags and metadata generation

### Unit Tests for `LLMClient`

Extend [backend/tests/unit/services/test_llm_client.py](/home/colutti/projects/personal/backend/tests/unit/services/test_llm_client.py) to cover:

- `stream_simple(...)` builds and propagates tracing config
- `stream_with_tools(...)` builds and propagates tracing config
- tracing helper failure does not interrupt response streaming
- expected metadata is attached when available

### Integration-Style Tests

Use mocks or fakes for LangSmith-facing behavior. Repository tests must not depend on live LangSmith access.

Validate:

- run names
- tags
- metadata payload assembly
- fail-open behavior when tracing operations raise exceptions

## Success Criteria

- Every main backend LLM execution produces a trace when tracing is effectively enabled.
- Dev and prod traces are isolated by project and credentials.
- Operators can locate a trace by user/session and inspect prompt, response, tool activity, latency, model resolution, and status.
- LangSmith downtime or misconfiguration does not affect end-user behavior.
- Existing internal prompt logging continues to function independently.

## Risks and Tradeoffs

- Full payload tracing increases privacy and compliance exposure.
- LangChain/LangSmith version compatibility may require careful implementation details.
- Capturing too much metadata redundantly can make traces noisy if not standardized.

These tradeoffs are acceptable for the selected goal of production debugging, provided environment isolation is enforced.

## Open Decisions Resolved in This Design

- Purpose: operational debugging
- Payload policy: full prompt/response visibility
- Scope: backend-wide tracing
- Failure mode: fail-open
- Environment model: isolated dev and prod projects with separate credentials
