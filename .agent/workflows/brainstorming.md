---
description: Brainstorming for feature or behavior changes before implementation
---

# Brainstorming Ideas Into Designs

Use this workflow when the request is exploratory, ambiguous, or large enough to benefit from a short design pass before code changes.

## Goal

Turn an idea into an implementation-ready design grounded in the current repository.

## Process

1. Explore the current project context first.
2. Ask focused clarifying questions when requirements are unclear.
3. Propose 2-3 approaches with trade-offs and a recommendation.
4. Present a concise design covering architecture, data flow, edge cases, and testing.
5. Save the approved design to `docs/plans/YYYY-MM-DD-<topic>-design.md` when the task merits persistent documentation.
6. If implementation will be multi-step, continue with `.agent/workflows/writing-plans.md`.

## Rules

- Read the codebase before proposing a design.
- Keep questions small and sequential.
- Scale the design to the task; not every change needs a long spec.
- Do not start implementation until the direction is clear enough to avoid rework.
- Prefer repository facts over assumptions from older docs.

## Minimum Design Checklist

- Problem statement
- Constraints
- Chosen approach and rejected alternatives
- Files or subsystems likely to change
- Test strategy
