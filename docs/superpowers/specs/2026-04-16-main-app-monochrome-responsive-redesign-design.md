# Main App Monochrome Responsive Redesign Design

**Status:** Draft for review
**Date:** 2026-04-16
**Scope:** `frontend/` main authenticated app only

## Goal

Redesign the main in-app experience to remove the current glassy, high-effect, purple-tinted visual language and replace it with a stricter monochrome dark system that remains mobile-first while making substantially better use of space on 1080p, 1440p, and 4K desktop displays.

The redesign must prioritize the authenticated app surfaces, especially dashboard and chat. Onboarding is out of scope unless a shared shell or token change requires light compatibility work.

## Why This Work Is Needed

The current UI language relies heavily on:

- blurred backgrounds
- semi-transparent surfaces
- ambient glow effects
- indigo/purple accents as structural color
- desktop layouts that often behave like enlarged mobile stacks

This creates three product problems:

1. The app feels visually noisy and less intentional than the desired reference direction.
2. The desktop experience does not convert additional screen space into better task flow.
3. The visual system is inconsistent across internal pages because style decisions are often encoded per-component instead of through a small number of shared rules.

## Product Direction

### Visual Direction

The new design language should be:

- dark monochrome by default
- based on black, graphite, white, and grayscale steps
- driven by contrast, spacing, rhythm, and layout hierarchy rather than effects
- quiet and athletic, closer to utility tooling than premium-glass marketing UI

The new design language should avoid using:

- decorative blur as a primary visual device
- gradient backgrounds for core app surfaces
- colored glow, haze, or ambient lighting
- purple/indigo as a foundational brand layer inside the app shell
- wide translucent cards used to imply depth

### Accent Color Policy

Accent color remains allowed, but only as a functional exception. It should be used sparingly for:

- success and improvement states
- error and warning states
- active chart series or selected data emphasis
- primary CTA emphasis when grayscale alone is insufficient

Accent color must not carry the layout or define the atmosphere of the screen.

## Scope

### In Scope

- shared app shell for authenticated main app routes
- visual token reset for the main app
- shared surface, border, spacing, and density conventions
- responsive layout strategy for internal app pages
- dashboard structural redesign
- chat structural redesign
- alignment pass on other in-app screens where the shell or base tokens affect them

### Out of Scope

- admin app
- marketing landing pages unless shared tokens force narrow compatibility fixes
- broad onboarding redesign
- backend changes
- feature scope changes unrelated to presentation and layout

## Success Criteria

The redesign is successful when:

- the app no longer reads as glassmorphic or purple-led
- desktop usage on 1080p already feels intentionally designed rather than stretched
- 1440p and 4K layouts use additional space for structure, not empty margins
- dashboard becomes a clearer control surface
- chat becomes easier to read and gains useful persistent context on larger screens
- mobile remains first-class and is not harmed by desktop improvements

## Design Principles

### 1. Mobile First, Not Mobile Only

Mobile remains the default flow and the first constraint for composition. Desktop layouts are not allowed to simply scale the mobile stack. They must introduce structure where extra width adds comprehension or speed.

### 2. Solid Surfaces

Primary app surfaces should use solid or near-solid fills with subtle border separation. Depth should come from nesting, spacing, and tonal steps rather than transparency and blur.

### 3. Width With Intent

Wider screens should gain:

- additional columns
- persistent context panels
- grouped summaries
- tighter reading widths for text-heavy areas

Wider screens should not gain:

- arbitrarily larger bubbles
- oversized empty gutters
- center-only content floating in excess space

### 4. Reusable System Before Local Fixes

The redesign should start from tokens, shell rules, and a small set of shared component conventions. Per-page cleanup alone would recreate inconsistency.

### 5. Density by Surface Type

Not all screens should share the same density:

- dashboard should feel like a compact decision surface on desktop
- chat should protect message readability while exposing optional side context
- forms and settings can stay looser than analytics surfaces

## Responsive Strategy

The redesign should establish explicit behavior by resolution class instead of relying mostly on `md` breakpoints.

### Mobile

- single-column flows
- bottom navigation remains primary
- focused content stacks
- no extra side panels

### 1080p Desktop

- treated as the minimum serious desktop target
- top-level shell should feel stable and deliberate
- key pages may move to two-zone layouts
- content should no longer appear as a mobile column centered inside a large monitor

### 1440p Desktop

- introduce more breathing room between major zones
- allow dashboards and data-heavy pages to split into primary and secondary columns
- allow chat to add persistent side context

### 4K and Ultrawide

- avoid a single stretched center column
- distribute content into multiple coordinated zones
- constrain reading widths inside each zone
- keep the page feeling anchored and useful rather than sparse

## Shared System Changes

### 1. Theme Tokens

The main app theme should be redefined around:

- background levels
- surface levels
- border levels
- text hierarchy
- state colors
- layout widths
- spacing scales

The following existing ideas should be retired or replaced in the main app:

- `glass-card`
- heavy `backdrop-blur`
- gradient-led token names
- premium-only visual abstractions used as default app primitives

New tokens should describe intent instead of effect, for example:

- app background
- elevated surface
- subtle border
- strong text
- muted text
- workspace max widths
- reading widths

### 2. App Shell

The authenticated shell should be refactored to support:

- a calmer desktop top bar
- less decorative chrome
- consistent padding bands by breakpoint
- route-aware max widths instead of one global container rule

The shell must support multiple page width modes, for example:

- standard content width
- workspace width
- conversation width

This allows dashboard and chat to use space differently without each page fighting the same global container.

### 3. Shared Surfaces and Controls

Core shared UI should move to:

- solid cards
- lower corner-radius intensity where appropriate
- cleaner separators
- stronger typographic hierarchy
- more restrained hover and active states

Buttons, pills, tab bars, and drawers should all lose decorative blur and glow as default behavior.

## Dashboard Redesign

### Problems in the Current Dashboard

The current dashboard behaves like a visually rich bento stack that works on mobile but underuses desktop width. It also assigns similar visual weight to too many blocks at once.

Specific problems:

- hero block is visually loud
- charts and summary cards compete for attention
- desktop layouts rely mostly on simple grid expansion
- important context is present but not staged into clear primary and secondary zones

### Target Dashboard Behavior

The desktop dashboard should feel like a training control center.

### Mobile

- preserve stacked flow
- preserve quick scannability
- keep most current interaction patterns

### 1080p

- introduce a two-zone structure
- top summary remains prominent but calmer
- charts and key metric clusters should sit in clearer primary and secondary sections

### 1440p and Above

Use a three-zone layout:

- primary column for major progress and trend views
- secondary column for body composition and supporting charts
- tertiary rail for streak, recent PRs, alerts, targets, and short status blocks

The goal is to transform width into hierarchy.

### Dashboard Visual Direction

- remove gradient overlays from hero blocks
- replace glowy KPI styling with monochrome blocks and selective state accents
- reduce decorative chart framing
- use stronger contrast between major sections and supporting sections
- reduce the sense that every metric is competing to be the main event

### Dashboard Content Prioritization

The dashboard should explicitly separate:

- today and target information
- trend information
- body composition and progress
- recent achievements and status items

This grouping must be visible in the layout, not only in headings.

## Chat Redesign

### Problems in the Current Chat

The current chat already has a usable mobile structure, but desktop width is mostly consumed by a large central area plus a floating input. Large monitors increase width without increasing utility.

Specific problems:

- conversation width can become too generous
- desktop does not create persistent contextual support
- header and composer still inherit some of the glass-heavy visual language
- extra space does not help the user reason about trainer context, attachments, goals, or memory

### Target Chat Behavior

The desktop chat should become a workspace, not only a message feed.

### Mobile

- preserve current single-thread flow
- keep composer accessible and compact
- avoid adding panels that create cramped horizontal density

### 1080p

- constrain conversation reading width
- stabilize header and composer structure
- support a single secondary context panel only if it adds clear immediate value
- otherwise prefer a narrower central conversation workspace instead of filling the screen

### 1440p and Above

Adopt a multi-panel conversation layout:

- central conversation column
- right-side context panel with trainer, memory, goals, or conversation aids
- optional left-side conversation navigation only if existing product needs justify it

The central conversation must remain readable and should not expand simply because width exists.

### Chat Visual Direction

- remove decorative blur from header and composer
- use solid bars and surfaces
- reduce reliance on colored indicators except for status and warnings
- give attachments, upload states, and assistant status a cleaner operational appearance

### Chat Context Panel

The context panel should be designed so that it can host product-relevant support content over time, for example:

- current trainer summary
- relevant body or goal context
- memory snippets
- suggested prompts
- recent linked actions

The spec does not require all of these to be built immediately. It requires the layout to make room for them in a coherent way.

## Other In-App Pages

Although dashboard and chat are primary, the redesign must not stop there. Other internal pages should inherit the new system well enough that the app no longer feels split between new and old design languages.

Expected outcomes for secondary pages:

- cleaner shell fit
- monochrome surfaces
- better desktop spacing rules
- more intentional max widths
- fewer decorative effects

This is a consistency requirement, not a full page-by-page redesign mandate at the spec level.

## Implementation Constraints

- keep the app mobile-first
- do not break onboarding flows unnecessarily
- prefer shared-system changes before heavy one-off page CSS
- avoid introducing a parallel design system just for a few routes
- keep responsive rules understandable and maintainable

## Testing and Validation Expectations

The implementation should validate at minimum:

- visual stability on mobile widths
- dashboard usability on 1080p and 1440p
- chat readability and structure on 1080p and 1440p
- acceptable behavior on very wide screens
- no regression in shell navigation or route layout

Automated verification should include the required frontend lint and typecheck gates. Additional UI test coverage should be added where behavior or structure changes are testable in a stable way.

Manual product review should explicitly inspect:

- dashboard on mobile and desktop
- chat on mobile and desktop
- at least one representative secondary in-app page

## Risks

### 1. Token Migration Drift

If old premium utilities remain mixed with new surface rules, the redesign will look inconsistent. The implementation plan must identify and replace foundational utilities instead of only layering overrides.

### 2. Desktop Overcorrection

It is possible to overuse desktop width and create layouts that are technically denser but harder to scan. Reading widths and primary/secondary emphasis must remain controlled.

### 3. Shared Shell Regressions

Changing the shell can affect many pages at once. This work should be staged carefully and validated route-by-route.

## Proposed Rollout Order

1. establish new main-app tokens and shared surfaces
2. refactor authenticated shell to support width modes
3. redesign dashboard structure
4. redesign chat structure
5. align secondary in-app pages to the new system where shared changes are not enough

## Non-Goals

This redesign is not intended to:

- rebrand the company
- rebuild the admin
- add new product modules
- redesign the landing site
- change business logic

## Final Design Summary

The main app should move from a decorative premium-glass interface to a restrained monochrome workspace system. The redesign should preserve mobile quality while making desktop genuinely useful. Dashboard becomes a command surface, chat becomes a structured workspace, and the app shell becomes a stable foundation that uses width intentionally across 1080p, 1440p, and 4K displays.
