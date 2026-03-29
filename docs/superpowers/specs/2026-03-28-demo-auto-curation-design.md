# Demo Auto-Curation Design

Date: 2026-03-28
Status: Approved for planning

## Goal

Replace manual per-message review for the demo user with an automatic curation flow that:

- reads the source user from production in read-only mode
- groups chat history into episodes instead of isolated messages
- selects the 20 best episodes by product coverage
- reduces each selected episode automatically
- publishes the result to the demo account
- lets the operator prune bad messages or full episodes from the published demo inside admin

The operator's review happens by opening the real demo account in the app, not by approving raw JSON before publish.

## Problem Statement

The current export pipeline produces too much chat to review manually. In the source snapshot, 3 months of activity generated 1,687 chat messages across 71 active days. That volume is too high for a human curation pass and creates unnecessary friction before the demo can be used.

The demo needs to feel rich and real, but the curation workflow must stay operationally lightweight. The unit of review must become an episode of product value, not an individual message.

## Constraints

- Production remains read-only. No step may write to the source environment.
- The published demo user remains read-only across the app.
- The first pass should optimize for speed to a usable demo, not perfect editorial tooling.
- The published demo should favor product coverage over raw volume or recency.
- Operators do not want a mandatory pre-publish review queue.
- Pruning from admin should delete content from the published demo dataset, not just hide it.
- The system should stay compatible with the existing `message_store` chat persistence used by the app.

## Product Decision Summary

- Use a single manual snapshot source, not automatic sync.
- Keep the source window at 3 months.
- Auto-select 20 episodes for the first published demo.
- Reduce messages automatically inside each selected episode before publish.
- Rank episodes by coverage of product surfaces rather than by conversation length or novelty alone.
- Publish directly to the demo account, then prune while viewing the real app experience.
- Support admin deletion at both episode and individual message level.

## Non-Goals

- No pre-publish moderation UI for message-by-message approval.
- No reversible "soft hide" for demo pruning in the first version.
- No dynamic runtime episode generation inside the app.
- No attempt to support live chat sending for the demo user in this phase.
- No attempt to rebuild full vector memory or Qdrant state in this phase unless added explicitly in a later step.

## Chosen Approach

Use a materialized snapshot pipeline with four major data phases:

1. Export raw source data from production.
2. Segment chat into episodes and score them.
3. Reduce and sanitize only the selected episodes.
4. Publish a materialized demo dataset plus episode/message metadata for admin pruning.

This keeps the demo deterministic and easy to operate. The app continues reading standard published demo data, while the admin gets enough metadata to inspect and delete unwanted content without needing a second review system.

## Alternatives Considered

### 1. Keep reviewing raw messages before publish

Rejected because the source volume is too high. Even after basic filtering, reviewing hundreds or thousands of messages is not a practical operating model.

### 2. Publish a hidden staging dataset and require a promotion step

Rejected for now because it adds operational complexity without solving the core pain point. The operator wants to evaluate the demo in the real app and prune visually.

### 3. Build the demo view dynamically from source data plus exclusions

Rejected because it complicates runtime reads, admin actions, and debugging. A materialized published snapshot is simpler and safer for the first version.

## Pipeline Design

### 1. Export

The existing export step remains the start of the flow:

- load production connection info from `.env.prod`
- connect read-only to Mongo
- export the source user profile and related logs for the last 3 months
- export raw `message_store` data for the source user

This continues to produce a raw artifact set for traceability.

### 2. Segment

Add a segmentation step that groups `message_store` items into candidate episodes.

Initial segmentation rules:

- sort messages chronologically
- start a new episode when the time gap exceeds a fixed threshold, initially 60 minutes
- preserve original message ids and timestamps
- record trainer distribution and turn counts per episode

An episode is the new unit of selection and pruning.

### 3. Classify

Each episode receives lightweight metadata used by ranking:

- `started_at`, `ended_at`
- `message_count`
- `human_count`, `ai_count`
- `trainer_types`
- `primary_domain`
- links to nearby structured events such as workouts, nutrition logs, and weight logs
- continuity signals such as explicit follow-up or progress discussion

`primary_domain` should be inferred heuristically from trainer type, nearby structured logs, and message content markers. The categories for v1 are:

- `workout`
- `nutrition`
- `weight`
- `memory`
- `checkin`
- `mixed`

### 4. Rank

Episodes should be ranked by product coverage and demo usefulness, not by size alone.

Positive signals:

- clear back-and-forth between user and coach
- compact beginning-middle-end structure
- connection to structured logs near the same period
- presence of coaching adjustment, explanation, or continuity
- contribution to underrepresented product domains

Negative signals:

- extremely long conversations
- repeated conversations of the same type
- operational or low-information exchanges
- monologues without strong product value

Selection should use quotas instead of taking the top 20 by score alone. The initial target mix is:

- 5 `workout`
- 4 `nutrition`
- 3 `weight`
- 3 `memory` or `checkin`
- 2 `course-correction` style episodes detected by heuristic markers
- 3 wildcard slots for the best remaining episodes

If a quota cannot be filled, the remaining slots fall back to the next best episodes by score.

### 5. Reduce

After episode selection, reduce the message list inside each chosen episode.

Reduction goals:

- keep the main coaching arc intact
- keep enough user context for the AI replies to make sense
- remove repetitive, operational, or low-signal turns
- target 4 to 10 published messages per episode in normal cases

The first version should use deterministic heuristics rather than an LLM rewrite pass. That keeps the pipeline cheaper, easier to debug, and safer against hallucinated edits. Rewriting should remain limited to sanitization, not summarization.

### 6. Sanitize

Apply mandatory sanitization before publish:

- rewrite email and account identifiers to the demo account
- strip direct personal identifiers and third-party secrets
- remove or rewrite obvious private content in selected messages
- preserve trainer metadata and timestamps only where they help the demo

The sanitization layer should operate on already selected and reduced content, not on the full raw export.

### 7. Publish

Publish directly to the demo account in the target environment:

- published profile marked `is_demo=true`
- structured logs remapped to the demo email
- reduced chat messages written to `message_store`
- episode/message metadata written to demo curation collections

The publish step should replace the prior published demo dataset for that demo account so reruns stay deterministic.

## Data Model

Add explicit metadata collections for the demo snapshot and its published chat structure.

### `demo_snapshots`

Fields:

- `snapshot_id`
- `source_user_email`
- `demo_email`
- `window_start`
- `window_end`
- `selection_strategy`
- `episode_count`
- `message_count`
- `created_at`

### `demo_episodes`

Fields:

- `snapshot_id`
- `episode_id`
- `title`
- `started_at`
- `ended_at`
- `primary_domain`
- `trainers`
- `source_message_ids`
- `published_message_ids`
- `score`
- `status`

`status` starts as `published` and becomes `deleted` when pruned from admin.

### `demo_messages`

Fields:

- `snapshot_id`
- `episode_id`
- `message_id`
- `role`
- `trainer_type`
- `timestamp`
- `content`
- `source_message_id`
- `status`

`status` starts as `published` and becomes `deleted` when pruned from admin.

### `demo_prune_log`

Fields:

- `snapshot_id`
- `episode_id` optional
- `message_id` optional
- `action`
- `performed_by`
- `performed_at`

This log exists for auditability even though the published data deletion is definitive for the demo dataset.

## Admin Design

Extend admin with demo-curation tooling focused on deletion, not editing.

### Demo User Overview

When viewing the demo user in admin, show:

- demo badge
- current published snapshot id
- active episode count
- active message count
- link to open the main app as the demo user

### Episode List

Provide a list of published episodes for the current snapshot showing:

- title
- date range
- primary domain
- trainer set
- published message count
- selection score

Actions:

- open episode detail
- delete episode

### Episode Detail

Provide a chronological message list for one episode showing:

- role
- trainer
- timestamp
- content

Actions:

- delete message

Deleting an episode removes its published messages from the demo dataset and updates the curation metadata accordingly.

## App Behavior

The main app should continue to behave like a standard read-only demo account:

- historical chat is visible
- no new messages can be sent
- structured progress surfaces remain visible
- removed messages or episodes simply stop appearing after admin deletion

The app does not need a special review mode.

## Files and Subsystems Likely To Change

Main backend:

- `backend/scripts/build_demo_snapshot.py`
- `backend/scripts/demo_snapshot_lib.py`
- `backend/src/repositories/*` for demo curation persistence
- `backend/src/services/*` for segmentation, ranking, publish, and prune logic
- `backend/src/api/endpoints/*` for demo curation admin APIs if exposed from main backend

Admin backend:

- `backend-admin/src/api/endpoints/admin_users.py`
- new admin endpoints for snapshot, episode, and message deletion flows

Main frontend:

- no major new surface required beyond existing demo behavior
- optional deep link support from admin into the demo account

Admin frontend:

- `frontend/admin/src/features/admin/components/*`
- new pages or panels for snapshot overview, episode list, and episode detail

## Error Handling

- If export returns no user or no chat data, fail with a clear source-user error.
- If segmentation produces too few useful episodes, publish fewer than 20 and record why.
- If sanitization removes all messages from an episode, exclude that episode before publish.
- If publish partially fails, the demo account should not be left with mixed old and new snapshot state.
- If admin deletion fails, keep the published view unchanged and show explicit failure feedback.

## Testing Strategy

### Pipeline

- segmentation creates stable episodes from raw chronological messages
- ranking prefers coverage and respects quotas
- reduction preserves alternating user/AI flow where available
- sanitization removes demo-forbidden fields and identifiers
- publish writes deterministic episode/message metadata

### Backend APIs

- demo curation admin endpoints list snapshots and episodes correctly
- deleting an episode removes its published messages
- deleting a message updates both published data and curation metadata
- demo read-only protections continue to block normal user writes

### Admin Frontend

- demo overview renders snapshot metadata
- episode list renders counts and delete actions
- episode detail renders messages and supports single-message deletion
- deletion updates the visible state correctly

### Main App

- published demo still renders chat history and structured data
- pruned content no longer appears
- read-only restrictions remain intact

## Open Assumptions

- The first published auto-curated demo targets about 20 episodes and roughly 90 to 180 total messages.
- The source of truth for demo chat remains Mongo `message_store`.
- Qdrant or vector-memory replication stays out of scope for this pass unless promoted into implementation scope explicitly.
