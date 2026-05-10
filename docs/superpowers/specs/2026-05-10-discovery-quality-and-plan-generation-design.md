# Design: Discovery Quality and Plan Generation

## Problem

The plan_specialist LLM generates plans with only 2 exercises per routine (e.g., Push: Supino reto + Desenvolvimento militar) despite having a 5-item discovery checklist. The root cause is not a schema, validation, or UI issue — it is a **prompt quality** problem:

1. The `_minimum_upsert_payload_template()` in `plan_tools.py` anchors the model with only **1 exercise per routine**, teaching the LLM that sparse plans are acceptable.
2. The `plan_specialist.md` prompt tells the model **how to build JSON** (call tool, get template, upsert) but never **what quality of content to provide**.
3. The `training_specialist.md` actively **prohibits** the training specialist from structuring plans, delegating to plan_specialist — but plan_specialist has zero training domain knowledge.
4. The `coach_reply.md` has no guardrails about plan claims or integration blame.

## Principles

- The AI decides what a complete plan is; we guide with domain knowledge in prompts, not hard-coded validation.
- The coach does discovery with the user; specialists are the "programmers" with domain knowledge.
- The plan_specialist is a **project manager** — orchestrates and persists, does NOT invent training or nutrition content.
- Training specialist must emit `training_recommendation`; nutrition specialist must emit `nutrition_recommendation`.
- The plan_specialist consumes those recommendations instead of inventing alone.
- If specialists haven't recommended anything material and the user asks for a plan, return `discovery_needed` instead of inventing.
- The plan_help() template must have realistic examples (6+ exercises), not 1 exercise.
- coach_reply must never affirm plan was saved without `upsert_plan` success, and never blame Hevy for internal plan content.
- No structural changes to graph, output_contract, validation, or schema — only prompts, templates, and docs.

## Design Decisions

### 1. Training Specialist: Domain Knowledge Provider

The training specialist already has access to Hevy routines, exercise search, and workout history. It must:
- Analyze user's training context (split preference, exercise history, goals)
- Recommend appropriate exercises, sets, reps, and load ranges
- Structure the recommendation in `technical_summary` as structured text
- Signal through existing `plan_signal` field when its recommendations conflict with the current plan

This is NOT a structural change — `technical_summary` already exists in the output contract. The plan_specialist already receives `training_analysis` as a context block.

### 2. Nutrition Specialist: Nutrition Targets Provider

The nutrition specialist already has access to metabolism data, tdee params, and nutrition history. It must:
- Calculate appropriate calorie targets and macro splits based on metabolism and goal
- Recommend meal structure, timing, and adherence strategies
- Structure the recommendation in `technical_summary`

The plan_specialist already receives `nutrition_analysis` as a context block.

### 3. Plan Specialist: Orchestrator

The plan specialist changes from "plan creator" to "plan orchestrator":
- It still drives discovery (5 items) and calls `plan_help` + `upsert_plan`
- But it reads `training_analysis` and `nutrition_analysis` from context blocks to populate training and nutrition content
- If a specialist has no material contribution (e.g., training specialist is no-op because user hasn't discussed training), the plan returns `discovery_needed` instead of inventing
- Before calling `upsert_plan`, it checks: did training and nutrition contribute? If not, don't proceed

### 4. Coach Reply: Guardrails

- Never claim plan was saved unless `upsert_plan` returned `SUCESSO_UPSERT_PLAN`
- Never blame Hevy or other integrations for internal plan content
- Never invent explanations for plan content that specialists didn't provide

### 5. Template: Realistic Anchoring

Replace the 1-exercise template with a proper Push/Pull/Legs split showing 6+ exercises per routine. This anchors the LLM to generate plans with adequate exercise volume.

## Files Changed

- `backend/src/services/agents/config/prompts/training_specialist.md`
- `backend/src/services/agents/config/prompts/nutrition_specialist.md`
- `backend/src/services/agents/config/prompts/plan_specialist.md`
- `backend/src/services/agents/config/prompts/coach_reply.md`
- `backend/src/services/plan_tools.py`
- `AGENTS.md`
- `docs/superpowers/specs/2026-05-10-discovery-quality-and-plan-generation-design.md`

## Out of Scope

- Structural changes to graph, output_contract, schema, or validation
- Frontend changes
- New tools
- New node types or routing logic
- Hard-coded exercise counts
