# Main App Unified Design System Redesign

Date: 2026-04-28
Scope: `frontend/` only
Register: product
Status: proposed

## Objective

Redesign the main app so every authenticated screen in `frontend/` follows one coherent product UI system derived from the new "Developer Performance Interface" guide provided by the user.

This is not a theme swap. The work must centralize styling, unify layout and interaction patterns, and reduce local page-specific styling so new screens inherit the correct appearance and behavior by default.

The redesign must apply to existing screens now, in one delivery, not as a phased migration.

## Why This Exists

The current frontend already has shared styling primitives, but they do not enforce enough consistency:

- global tokens in `frontend/src/index.css`
- shared visual helpers in `frontend/src/shared/styles/ui-variants.ts`
- base components such as `Button`, `Input`, and `PremiumCard`

Those foundations still coexist with many screen-level classes and local visual decisions. The result is drift between pages, especially across forms, listings, dashboard modules, onboarding blocks, and settings surfaces.

The user requirement is stronger than "make it look better":

- all main app screens must follow the same visual language
- structurally similar screens must use the same layout model
- creating new screens should require minimal manual styling
- changing the design system later should mostly happen in centralized primitives, not across many pages

## Product Scene

This UI serves users in short, task-focused coaching sessions, often on mobile and sometimes during low-light early morning or evening use. The interface should feel like a disciplined operational workspace: low-noise, high-clarity, dark-only, and immediately actionable.

The surface should communicate reliability and precision, not hype, novelty, or decorative "AI" aesthetics.

## Design Direction

### Visual Character

Use a restrained product-system approach:

- dark-only workspace
- neutral surfaces dominate
- one primary accent for critical actions and active state
- one success accent for positive state
- one warm accent for secondary categorization when necessary
- no decorative gradients, glow systems, or shadow-led depth

Hierarchy should come from:

- tonal surface separation
- strong typography contrast
- disciplined spacing
- thin structural borders
- predictable layout patterns

### Design Rules

- No screen should invent its own interaction vocabulary when a shared one exists.
- Similar tasks must use the same screen template.
- Shared components should own their default visual styling.
- Local `className` styling should be for layout exceptions or content-specific needs, not for re-skinning shared controls.
- The system should prefer full-surface cards, section blocks, and line-based separation over ornamental depth.
- New UI should avoid "premium" semantics in naming when the component is really a system primitive.

## Source Style Guide Translation

The user-provided guide maps into the app as follows.

### Color System

Adopt the provided surface stack and semantic colors as the primary token source:

- background and shell: near-black surface family
- content surfaces: stepped dark greys
- text: high-contrast off-white plus subdued secondary copy
- primary accent: indigo-blue for primary actions and focus
- secondary accent: green for positive/available/success cues
- tertiary accent: warm orange for controlled emphasis only
- error colors: dedicated error surface and text tokens

The existing monochrome-teal system should be replaced by this token set inside `frontend/`.

### Typography

Use Inter across the product UI with a compact product scale:

- hero-display
- headline-lg
- card-title
- body-md
- label-sm

Monospace accents may be introduced for code-like data, metrics, or dense numerical contexts where they improve comprehension.

### Spacing and Shape

Adopt the provided base-8 rhythm:

- base spacing token: 8px
- standard internal module spacing: 24px
- page gutter: 24px
- page margin rhythm: 40px
- max content width: 1280px

Rounded corners should stay disciplined and repeatable:

- most controls: 4px to 8px
- larger containers: 8px to 12px
- pills only where the component semantics justify it, such as small status indicators or selected nav chips

### Elevation

Depth is communicated through:

- surface tiers
- subtle outlines
- minimal hover state shifts

Depth is not communicated through:

- drop shadows as default
- large blur treatments
- glow decoration

## Architecture

The redesign should be implemented in four layers.

### 1. Global Tokens

Refactor `frontend/src/index.css` into the main token source for:

- color roles
- typography roles
- spacing scale
- radius scale
- border roles
- focus-ring roles
- semantic states
- surface tiers
- page-width and gutter roles

This file should define the system, not carry leftover compatibility aliases unless they are still required during migration. Any temporary compatibility tokens should be intentionally named and removed once consumers are updated.

### 2. Shared Styling Contract

Refactor `frontend/src/shared/styles/ui-variants.ts` so it becomes a semantic contract over the tokens rather than a collection of legacy "premium" shortcuts.

This layer should expose reusable class contracts for:

- page shell
- cards and surfaces
- headings and labels
- grid and stack rhythms
- badges and status treatments
- motion presets
- section spacing

If necessary, rename this module to better reflect a system-level role.

### 3. Base UI Components

Refactor current base components so they automatically render with the new design language:

- button
- input
- textarea
- select-like controls, if present
- date input
- card/surface
- pagination
- tabs or segmented selection patterns
- toast
- drawer panels
- empty state
- error boundary surface

Each interactive component must support:

- default
- hover
- focus-visible
- active
- disabled
- loading
- error where applicable

The goal is that a new instance of a shared component already looks correct before any local styling is added.

### 4. Screen Templates and Feature-Level Composition

This is the core of the redesign. Similar pages must stop re-implementing structure independently.

Create reusable screen-level composition patterns so data changes, but page grammar stays consistent.

## Required Shared Screen Templates

### EntityFormScreen

Used for create/edit flows across domains such as:

- workout creation or editing
- nutrition entry or editing
- body log creation or editing
- integration or settings forms when structurally similar

Behavior:

- standard page header
- sectioned form layout
- consistent field grouping rhythm
- consistent action placement
- optional sticky bottom action bar on mobile
- standardized validation and inline error presentation

Rule:

If two flows are both "enter or edit domain data", they should use this template unless there is a clear task-level reason not to.

### EntityListScreen

Used for list/index flows across domains such as:

- workouts
- nutrition items or history
- body logs
- plan collections
- settings sublists where structurally appropriate

Behavior:

- page header with title and primary action
- optional subtitle or summary line
- standard toolbar for search, filters, sort, and contextual actions
- consistent item density
- consistent row or card action placement
- shared empty state, loading skeleton, and pagination treatment

Rule:

If two screens are both "browse, filter, and act on a collection", they should use the same collection template and differ only in data rendering details.

### InsightScreen

Used for dashboard-like and progress-oriented surfaces such as:

- dashboard
- plan summary blocks
- body/progress trend views
- other metric-led decision screens

Behavior:

- consistent hierarchy between summary, trend, and action guidance
- repeated metric treatments
- restrained use of accent color
- predictable annotation and helper-copy tone

### ConversationScreen

Used for chat and other guided conversation surfaces.

Behavior:

- shared shell rules with the rest of the app
- message and composer hierarchy aligned to the same token system
- contextual panels, quick actions, and auxiliary controls use the same card, button, and chip vocabulary as the rest of the app

## Required New Shared Building Blocks

The redesign may require new components to avoid duplication. This is in scope and expected.

Create shared primitives where repeated patterns exist, including as needed:

- `AppShell`
- `PageHeader`
- `ScreenSection`
- `SectionHeader`
- `SurfaceCard`
- `Field`
- `FieldGroup`
- `FormSection`
- `StickyActionBar`
- `ListToolbar`
- `ListItemRow` or `ListItemCard`
- `MetricBlock`
- `StatusChip`
- `InlineNotice`
- `SkeletonBlock`

Naming can change during implementation, but the underlying responsibility should remain:

- shared structure
- shared state language
- shared spacing
- shared typography
- shared affordance rules

## Shell and Navigation

The shell itself must be brought into the same system:

- desktop top navigation
- mobile navigation
- page width management
- gutters
- content top spacing
- active-state appearance
- utility controls such as language selector and profile affordances

The shell should feel like part of the same disciplined product UI, not a separate design theme.

## Migration Strategy

This is a single-delivery migration for `frontend/`.

Recommended order:

1. Replace tokens and global utility roles.
2. Refactor shared base components.
3. Introduce new screen templates and shared building blocks.
4. Migrate the main shell and navigation.
5. Migrate feature screens to shared templates.
6. Remove obsolete local styles, legacy utility names, and now-redundant visual exceptions.

Even though delivery is single-pass, implementation should still move from foundation to consumers so consistency is enforced from below.

## Screens and Areas Affected

The redesign applies to all main app surfaces in `frontend/`, including but not limited to:

- dashboard
- chat
- plan
- workouts
- nutrition
- body
- onboarding
- settings
- integrations inside the main app
- shared drawers, dialogs, cards, notices, and empty states

No changes are required for `frontend/admin/`.

## Content and Interaction Consistency Rules

These rules are mandatory:

- An add/edit workout flow and an add/edit nutrition flow must share the same structural pattern when the job-to-be-done is equivalent.
- A list of workouts and a list of nutrition-related records must share the same listing grammar when the job-to-be-done is equivalent.
- Shared interaction states must look the same across screens.
- Copy hierarchy must remain compact and operational, not editorial.
- Focus states must be visible and consistent.
- Empty states must teach the next action, not simply announce absence.
- Loading states should prefer skeletons or in-place placeholders over arbitrary spinners where feasible.

## Non-Goals

This design does not include:

- admin app redesign
- backend changes unrelated to supporting existing frontend behavior
- product-scope expansion unrelated to visual and structural consistency
- visual experimentation that weakens familiarity for standard product tasks

## Testing and Verification Design

Because the redesign changes shared primitives and many consumers, testing must expand beyond a happy path.

### Automated Testing Expectations

Add or update tests for:

- base components whose visual state logic changes
- template-level shared components
- screens whose structure changes substantially
- responsive behavior where layout contracts change
- critical flows affected by new shared form and list templates

Test coverage should include:

- standard rendering
- interaction states when testable
- empty states
- error states
- loading states
- edge layouts on mobile and desktop where the template contract changes

### Required Validation Gate

Because this task touches `frontend/`, completion requires:

- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`

Additional frontend tests should be run according to the changed areas. If structural changes are broad enough, full frontend automated coverage should be revisited.

## Risks

### Risk: Superficial Theme Swap

If implementation only updates colors and button styles, visual drift between screens will remain.

Mitigation:

- enforce screen templates
- migrate consumers to those templates
- treat repeated local styling as a refactor target, not acceptable residue

### Risk: Over-Abstraction

If templates become too rigid, legitimate differences between domains may become awkward.

Mitigation:

- share structural grammar, not domain text
- allow slot-based composition inside templates
- keep data rendering flexible while enforcing spacing, hierarchy, and actions

### Risk: Partial Migration Leftovers

Legacy "premium" semantics, glassmorphism leftovers, and local color classes can undermine consistency.

Mitigation:

- identify legacy primitives early
- migrate consumers in one pass
- remove obsolete helpers once migration lands

## Implementation Readiness Criteria

This design is ready for planning when:

- the user approves this document
- the implementation plan decomposes the migration into safe execution steps
- each step preserves functional behavior while replacing visual structure

## Success Criteria

The redesign is successful when:

- the main app reads as one coherent product system across all screens
- structurally similar screens share the same templates and interaction grammar
- shared components own their correct default styling
- adding a new form or listing screen requires little or no custom visual styling
- future visual updates can be made primarily in centralized tokens and primitives
