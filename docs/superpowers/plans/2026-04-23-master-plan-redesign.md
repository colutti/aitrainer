# Master Plan Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace daily-operational plan model with a master plan model (goal + timeline + nutrition targets + weekly training program), always injected into prompt.

**Architecture:** Backend becomes source of truth for master plan snapshot and injects it in every prompt. Frontend Plan tab becomes read-only view of current master plan and rationale. Legacy fields and behaviors (`today_training`, `today_nutrition`, `upcoming_days`) are removed.

**Tech Stack:** FastAPI, Pydantic, MongoDB, React, Zustand, i18next, pytest, vitest.

---

## Execution Tasks

1. Refactor backend plan models and service snapshot formatter to new schema.
2. Update plan tools, prompt template, prompt builder usage and trainer flow.
3. Update plan endpoints and repository semantics for singleton overwrite-only behavior.
4. Refactor frontend plan types/store/ui to consume new payload.
5. Update locales (`pt-BR`, `en-US`, `es-ES`) for new plan language.
6. Remove obsolete legacy tests and add/adjust coverage for new model and rendering.
7. Run backend + frontend lint/type/test gates and document residual manual checks.
