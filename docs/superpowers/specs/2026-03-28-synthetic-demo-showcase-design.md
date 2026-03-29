# Synthetic Demo Showcase Design

Date: 2026-03-28
Status: Approved for planning

## Goal

Replace the current demo dataset derived from a real user with a fully synthetic demo account that:

- showcases the product from a marketing point of view
- stays grounded in capabilities that the software actually has
- uses a coherent aspirational persona instead of generic placeholder content
- publishes locally first for operator testing
- remains read-only across the system
- can later be translated into Portuguese and Spanish from the same base structure

The synthetic demo should feel like a polished real customer account, not a random sandbox and not a copy of the founder's production data.

## Problem Statement

The current demo dataset proves that the read-only mechanics and publish pipeline work, but it fails the actual product goal:

- the chat content is not compelling from a sales perspective
- the account still carries traces of the founder's identity and usage patterns
- the operator does not want to curate hundreds of inherited real messages
- the demo should intentionally highlight features such as Hevy, macros, plans, memory, and adaptive coaching rather than passively reflect whatever happened in a real account

The demo needs to stop being a sanitized copy and become a purpose-built showcase.

## Constraints

- The demo must only promise functionality that exists in the current product.
- The account must remain fully read-only in backend, frontend, and admin.
- The first publish target is the local development environment, not production.
- The demo must not expose the founder's name, email, photo, habits, or any other identifiable traces.
- The content should be deterministic enough to regenerate and refine without unpredictable model output.
- The chat, profile, dashboard, logs, and integrations state must support the same story.
- The first authored language is English.

## Product Direction

The demo becomes a hybrid showcase:

- one coherent aspirational user
- one believable narrative arc
- multiple deliberately chosen episodes that each demonstrate a different product capability

Tone and positioning:

- premium practical
- coach AI complete
- professional user persona
- English as the base authored language

## Persona

The synthetic demo user represents a disciplined busy professional who already trains consistently and wants clarity, continuity, and less friction.

Base persona:

- Display name: `Ethan Parker`
- Demo email for local publish: `demo@fityq.it`
- Age: 35
- Occupation style: product designer or tech lead
- Training frequency: 4 sessions per week
- Goal: body recomposition with a mild cutting bias while preserving performance
- Experience level: intermediate trainee
- Communication style: concise, thoughtful, not overly emotional

Why this persona:

- broad commercial appeal
- supports both performance and physique conversations
- makes integrations, macros, and planning feel natural
- fits the premium practical tone

## User Experience Target

When the operator opens the demo account in the app, the experience should communicate:

- this user has a clear goal and a real routine
- the coach remembers context and does not restart from zero
- the system connects chat decisions to actual workout, nutrition, and weight data
- integrations reduce friction rather than just existing as settings
- the dashboard confirms the same story shown in chat

The account should feel immediately useful within a few screens:

- chat history should contain strong proof points, not filler
- dashboard should show believable progress and momentum
- workout, nutrition, and weight tabs should all look populated and coherent
- the read-only state should remain obvious but non-disruptive

## Non-Goals

- No reuse of the founder's real messages as demo content.
- No requirement to preserve the previous episode-ranking system as the primary content source.
- No attempt to simulate unsupported features.
- No fully generative free-form LLM authoring at publish time.
- No multilingual publish in the first pass.
- No live write capability for the demo account.

## Chosen Approach

Build a deterministic synthetic demo generator that creates:

1. a synthetic profile and onboarding state
2. a scripted set of marketing-oriented chat episodes
3. structured logs for workouts, nutrition, weight, and prompt history
4. small but meaningful memory records
5. demo metadata compatible with admin pruning

Then publish that dataset locally through the existing demo publish flow, replacing the current derived local demo.

This keeps the already-built read-only protections, admin pruning, and publish mechanics, but swaps the source content from "curated copy" to "intentional showcase."

## Alternatives Considered

### 1. Keep the current real-data-derived dataset and only rewrite the chat

Rejected because it still leaves too much risk of personal traces in structured data and visual patterns. The goal is a synthetic demo, not a partially anonymized one.

### 2. Keep a real-data-derived structure and score better episodes

Rejected because better selection still does not solve the core problem: the content is not authored for product storytelling.

### 3. Create a tiny cinematic demo with only a handful of screens worth of data

Rejected because it would feel too staged when the operator explores dashboard, logs, or history depth. The demo should withstand normal browsing, not just a guided tour.

## Content Architecture

### Narrative Shape

The synthetic demo should cover roughly 8 to 12 weeks of progress and feel like one coaching block.

The story is:

- the user starts from a clear plan
- adopts the coach and integrations into an already busy routine
- gets real feedback from imported workouts and nutrition data
- handles friction and imperfect weeks without breaking consistency
- sees visible signs of progress in weight trend, performance, and adherence
- finishes with a confident next-step plan

### Chat Episode Set

The demo should ship with 12 authored episodes and roughly 90 to 130 total published chat messages.

Required episodes:

1. onboarding and coaching style selection
2. first weekly training structure
3. Hevy connection and first workout import
4. calorie and macro target setup
5. weight trend interpretation
6. busy-week training adjustment
7. recovery and fatigue adjustment
8. progress review after a few weeks
9. restaurant or travel nutrition scenario
10. consistency correction after a noisy stretch
11. performance win or PR reflection
12. next-block planning

Episode requirements:

- every episode must show a distinct product value
- every episode must read naturally without filler
- each episode should stay compact, typically 6 to 12 messages
- the coach should sound specific and observant, not motivational and generic

### Structured Data Shape

The authored chat must be backed by synthetic structured data.

Profile and onboarding:

- onboarding complete
- one trainer persona selected explicitly
- realistic anthropometrics and goal setup

Workout logs:

- around 4 sessions per week on average
- enough logs to power the dashboard and recent activity
- enough exercise detail to produce believable PRs and volume trend
- at least part of the narrative should imply Hevy-driven synchronization

Nutrition logs:

- 5 to 7 weeks of logs
- realistic macro adherence with some imperfect days
- enough signal for calorie target and macro discussion

Weight and composition logs:

- 8 to 12 weeks of entries
- believable short-term noise with a meaningful trend
- enough composition fields for weight and body evolution views

Memories:

- few in number
- high in relevance
- directly reflected later in chat continuity

Prompt logs:

- enough to make admin and internal inspection look active and coherent

### Integration Representation

The demo should show integrations as real product capabilities without needing a live third-party sync during operator review.

Hevy:

- the profile should look connected
- workout logs should support the story that workouts were imported or synced
- one episode must explicitly reference the coach reacting to imported training data

Telegram:

- can remain available in the product state
- should not be a central narrative pillar in the first version

Memory:

- should appear as continuity in chat and as listable memory items
- should remain small and curated

## Data Authoring Strategy

The generator should not improvise freely. It should use controlled authored content.

Recommended structure:

- one persona definition file
- one episode catalog with message templates and metadata
- one deterministic structured-data generator that creates logs aligned to the narrative
- one publisher that materializes the synthetic dataset into the same local collections already used by the app

The authored text should live in editable data files rather than being buried in Python logic. This makes the demo maintainable by changing copy without rewriting generation code.

## Pipeline Design

### 1. Generate Synthetic Demo

Create a new pipeline command that generates a synthetic snapshot from authored inputs.

Inputs:

- persona definition
- episode definitions
- structured-data scenario parameters
- demo email and locale

Outputs:

- synthetic profile
- synthetic trainer profile
- synthetic workout logs
- synthetic nutrition logs
- synthetic weight logs
- synthetic memory items
- synthetic prompt logs
- synthetic chat messages
- synthetic demo snapshot metadata

### 2. Publish Local Demo

Reuse the existing publish path as much as possible, but publish from the synthetic snapshot artifact instead of the curated real-data artifact.

Publish behavior:

- replace the current local demo dataset for the selected demo email
- write `users`, logs, and `message_store`
- write `demo_snapshots`, `demo_episodes`, and `demo_messages`
- preserve `is_demo=true`

### 3. Prune in Admin

Keep the new admin pruning flow unchanged.

After local publish, the operator can:

- inspect episodes in admin
- delete episodes
- delete messages
- reload the app and see the result immediately

## Data Model

The existing demo metadata model remains valid, with one important semantic change:

- `source_user_email` no longer represents a production user origin
- for synthetic snapshots it should identify the authored scenario source, for example `synthetic:ethan-parker:v1`

Collections used:

- `users`
- `trainer_profiles`
- `workout_logs`
- `nutrition_logs`
- `weight_logs`
- `prompt_logs`
- `message_store`
- `demo_snapshots`
- `demo_episodes`
- `demo_messages`
- `demo_prune_log`

Possible metadata additions:

- `scenario_id`
- `locale`
- `persona_name`
- `content_version`

These fields help future translation and iteration without changing the core app behavior.

## Identity Safety Requirements

The synthetic demo must remove every meaningful trace of the founder.

This includes:

- display name
- profile photo
- chat language patterns that clearly derive from the founder's usage
- structured logs copied from the founder
- memory content copied from the founder
- timing patterns that only exist because of the founder's real data

The correct implementation strategy is replacement, not sanitization.

## Authoring Rules

The copy should follow these rules:

- English only for the first version
- concise and high-signal
- specific references to workouts, macros, schedule, fatigue, and progress
- no exaggerated claims
- no generic “great job, keep going” filler unless tied to real context
- no product promises beyond what the current codebase supports

The coach should feel like:

- observant
- structured
- calm
- useful under time pressure

## Testing and Acceptance

### Functional Acceptance

The local demo is acceptable when:

- the account opens successfully in the local app
- the account clearly presents `Ethan Parker`, not the founder
- chat history reads like a premium synthetic showcase
- dashboard and logs support the same story the chat tells
- the account remains read-only everywhere
- admin pruning still works on the synthetic content

### Verification

At minimum, implementation should verify:

- synthetic generator output schema
- publish into local Mongo
- `is_demo` preserved on the published user
- chat history load for the demo account
- write attempts still fail with `demo_read_only`
- admin episode and message deletion still works

## Rollout

Phase 1:

- ship the English synthetic demo locally
- validate the content in the app
- prune weak messages or episodes in admin

Phase 2:

- refine authored copy and data based on operator review
- stabilize a `v1` scenario

Phase 3:

- derive Portuguese and Spanish variants from the same scenario structure

## Open Decisions Resolved

- demo style: hybrid showcase
- tone: premium practical
- main value proposition: coach AI complete
- persona style: aspirational professional
- base language: English
- initial publish target: local environment
- content strategy: fully synthetic
