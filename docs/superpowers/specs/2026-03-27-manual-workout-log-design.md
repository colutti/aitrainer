# Manual Workout Log Design

Date: 2026-03-27
Status: Approved for planning

## Goal

Add a manual workout logging flow for end users that feels intuitive, uses the same lateral drawer pattern already present in nutrition and body flows, and preserves compatibility with the current Hevy-oriented workout data model.

This first version covers only manual logging of an executed workout session. It does not introduce workout plans, templates, or a global exercise catalog.

## Product Decision Summary

- Start with manual logging now.
- Keep the current `workout_logs` persistence model compatible with Hevy imports.
- Treat the new UI as an editor for an executed workout session, not as a planner.
- Use a hybrid input model:
  - free manual entry is always allowed
  - the UI suggests previous exercises from the user's own history
- Optimize for fidelity over speed.

## Non-Goals

- No weekly AI workout plan in this phase.
- No new database entity for workout templates.
- No global predefined list of workouts.
- No mandatory global exercise catalog.
- No attempt to merge "planned workout" and "executed workout" into one record type.

## Data Model Direction

The existing workout model already matches the target concept well:

- workout date
- workout type
- workout duration
- list of exercises
- each exercise containing per-set data
- optional source metadata

The manual flow should continue saving a standard workout log shaped like the current backend model so manual entries and Hevy-imported entries remain compatible in downstream stats, history, and future AI analysis.

### Data Implications

- Manual entries should save with `source="manual"`.
- Manual entries should not require `external_id`.
- The form structure should map cleanly to the existing `ExerciseLog` format:
  - `name`
  - `sets`
  - `reps_per_set`
  - `weights_per_set`
  - `distance_meters_per_set`
  - `duration_seconds_per_set`

## UX Direction

The workout page remains the history/list view. Creation and editing happen in a right-side drawer, matching the existing app pattern used in nutrition and body flows.

### Primary Page Behavior

- Keep the current workouts history page as the main surface.
- Add a clear primary CTA to create a manual workout log.
- Preserve the current pattern of selecting a workout from the list for detail/edit behavior.

### Drawer Structure

The drawer should be organized into three main sections:

1. Workout details
2. Exercises
3. Sticky footer actions

### Section 1: Workout Details

Fields:

- `date`
- `workout_type`
- `duration_minutes`

Behavior:

- Default date should be today.
- `workout_type` should support free text, with lightweight suggestions from the user's prior workout types.
- Duration remains optional at the data level, but the UI may encourage filling it.

### Section 2: Exercises

This is the core of the experience. Each exercise is represented by an expandable card.

Each exercise card header should show:

- exercise name
- number of sets
- optional quick summary such as total volume

Each exercise card body should support:

- editing the exercise name
- per-set rows
- add set
- duplicate last set
- remove set
- remove exercise

### Exercise Name Entry

Exercise names should be entered via a free-text field with autosuggest from the user's own prior exercise history.

Source of suggestions:

- previously imported Hevy workouts
- previously manually logged workouts

Behavior:

- user can always type a new exercise name not seen before
- suggestion system is assistive, never restrictive
- no requirement to maintain a large predefined exercise catalog

### Set Row Structure

Each set row should support high-fidelity logging and remain compatible with the current backend shape.

Visible-by-default fields:

- set number
- reps
- weight

Optional fields:

- duration
- distance

Recommended behavior:

- default a newly added exercise to one starter set
- allow duplicating the previous set to reduce repetitive typing
- keep optional cardio-style fields collapsed or secondary unless used

### Sticky Footer Actions

Footer actions should stay visible while scrolling:

- `Cancel`
- `Save workout`

If editing is added in the same phase, the same drawer can support both create and edit states using the existing drawer pattern already used elsewhere in the app.

## Suggested Acceleration Features

These are in scope if they stay lightweight and do not require new backend entities:

- suggest prior workout types
- suggest prior exercise names
- "duplicate previous set" within an exercise
- optional "duplicate recent workout" action if implementation cost remains low

Recommendation:

- Prioritize exercise-name suggestions first.
- Treat "duplicate recent workout" as secondary, not required for the first pass.

## Future Compatibility With AI Workout Plans

This design must explicitly preserve a clean upgrade path for a future AI-generated weekly workout plan.

The future model should separate:

- planned workout item
- executed workout log

Expected future flow:

1. AI generates the user's weekly workout plan.
2. The UI displays scheduled workout items.
3. The user taps a planned workout to execute it.
4. The same manual workout drawer opens prefilled.
5. The user adjusts what was actually performed.
6. Saving creates a normal `workout_log`.
7. The plan item may then be marked completed.

Important rule:

The manual workout drawer must be designed so it can later accept prefilled data without being conceptually tied to planning in this first phase.

## Error Handling

The flow should handle these cases clearly:

- save failure due to API/network error
- invalid set input
- empty workout with no exercises
- partial exercise with missing required set information

Recommended UX behavior:

- field-level validation for required inputs
- prevent save if there are no exercises
- keep drawer state intact on failed save
- show non-destructive error feedback

## Testing Direction

### Frontend

- drawer open/close behavior
- workout details validation
- add/remove exercise behavior
- add/remove/duplicate set behavior
- autosuggest behavior for prior exercise names
- successful save payload shape
- error state preservation on failed save

### Backend

- create manual workout with `source="manual"`
- ensure manual payload maps correctly to current `WorkoutLog`
- ensure missing `external_id` remains valid

## Open Constraints Resolved In This Design

- The product should not start with a predetermined global workout list.
- The suggestion source should come from the user's own history.
- The first version should optimize for fidelity, not minimal logging speed.
- The future AI weekly plan should reuse this drawer through prefilling rather than replacing it.

## Recommended Implementation Boundary

This design is focused enough for one implementation plan:

- manual workout create/edit drawer UX
- user-history-based exercise suggestions
- save path using the current workout log model

The AI weekly planning layer is intentionally excluded and should be designed separately later.
