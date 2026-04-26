---
name: FityQ
description: Monochrome coaching workspace that prioritizes clear action and measurable progress.
colors:
  app-bg: "#050505"
  app-surface: "#0d0d0d"
  app-surface-raised: "#141414"
  app-border: "#232323"
  text-primary: "#fafafa"
  text-secondary: "#b5b5b5"
  text-muted: "#7a7a7a"
  accent-action: "#14b8a6"
  accent-action-hover: "#0d9488"
  state-success: "#22c55e"
  state-warning: "#f59e0b"
  state-error: "#ef4444"
typography:
  display:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 900
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 700
    lineHeight: 1.15
  title:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Inter, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.2em"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  surface: "24px"
  pill: "999px"
spacing:
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent-action}"
    textColor: "{colors.app-bg}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.accent-action-hover}"
    textColor: "{colors.app-bg}"
    rounded: "{rounded.md}"
  button-secondary:
    backgroundColor: "{colors.app-surface-raised}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "0 24px"
    height: "44px"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "40px"
  input-default:
    backgroundColor: "{colors.app-surface-raised}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xl}"
    padding: "0 12px"
    height: "44px"
  card-surface:
    backgroundColor: "{colors.app-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.surface}"
    padding: "24px"
  nav-pill-active:
    backgroundColor: "rgba(255,255,255,0.1)"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.pill}"
    padding: "8px 24px"
---

# Design System: FityQ

## 1. Overview

**Creative North Star: "The Night Shift Coaching Console"**

This system is built for users checking plans, workouts, and recovery in short, high-focus sessions, often early morning or late evening. The interface behaves like an instrument panel, low glare, high contrast, and explicit next actions.

The visual personality follows PRODUCT.md directly: practical, intelligent, and accountable. Surfaces stay quiet and monochrome so recommendation moments and critical actions carry visual authority. The system explicitly rejects noisy motivational aesthetics, sterile medical bureaucracy, badge-first gamification, and over-designed "AI" styling.

**Key Characteristics:**
- Monochrome-first workspace with one action accent.
- Dense but readable hierarchy tuned for decision speed.
- Tactile controls with clear state feedback.
- Flat-by-default depth model with restrained lift cues.
- Utility copy and labels that prioritize action clarity.

## 2. Colors

The palette is restrained: dark neutrals carry almost all surface area, with a single teal action accent used only for primary intent.

### Primary
- **Teal Command** (`#14b8a6`): Primary actions, high-priority confirms, selected progress affordances.

### Secondary
- **Teal Pressed** (`#0d9488`): Hover and active feedback for primary action controls.

### Neutral
- **Midnight Base** (`#050505`): Global app background and shell framing.
- **Graphite Surface** (`#0d0d0d`): Default containers and content planes.
- **Raised Graphite** (`#141414`): Inputs, elevated states, and secondary buttons.
- **Quiet Divider** (`#232323`): Structural borders and separation lines.
- **Signal White** (`#fafafa`): Primary text and iconography.
- **Support Gray** (`#b5b5b5`): Secondary copy and labels.
- **Tertiary Gray** (`#7a7a7a`): Quiet metadata and low-emphasis annotations.

### Named Rules
**The Single Accent Rule.** The primary accent is reserved for explicit actions and selected state confirmation, never for decorative fills.

## 3. Typography

**Display Font:** Inter (with system-ui, sans-serif fallback)  
**Body Font:** Inter (with system-ui, sans-serif fallback)  
**Label/Mono Font:** Inter (uppercase label treatment)

**Character:** Compact, technical, and direct. Typography is optimized for glanceability in operational flows, not editorial expression.

### Hierarchy
- **Display** (900, `3rem`, 1.05): Hero numeric values and major page moments.
- **Headline** (700, `2rem`, 1.15): Primary section headings and key screen titles.
- **Title** (700, `1.25rem`, 1.25): Card and module titles.
- **Body** (400, `0.875rem`, 1.5): Main explanatory and supporting copy, capped to 65-75ch where long-form text appears.
- **Label** (800, `0.75rem`, `0.2em` tracking, uppercase): Micro-labels, state tags, and compact metadata.

### Named Rules
**The Operator Density Rule.** Use short, high-contrast text blocks and avoid paragraph-heavy sections in decision-critical screens.

## 4. Elevation

Depth is flat by default, with layering communicated primarily through tonal changes (`#0d0d0d` to `#141414`) and border contrast (`#232323`). Shadows are present only as subtle state feedback in navigation and badges.

### Shadow Vocabulary
- **Soft Lift** (`box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35)`): Floating mobile navigation shell.
- **Micro Emphasis** (`box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25)`): Compact badge and active pill emphasis.

### Named Rules
**The Flat-By-Default Rule.** Resting surfaces stay flat, lift appears only when state needs to be acknowledged.

## 5. Components

### Buttons
- **Shape:** Medium rounding (`8px`) for standard CTAs, large icon pills on navigation controls.
- **Primary:** Teal action fill (`#14b8a6`) with dark text (`#050505`), height (`44px`), horizontal padding (`24px`).
- **Hover / Focus:** Hover shifts to pressed teal (`#0d9488`), focus uses a soft white ring (`2px` with 30% opacity).
- **Secondary / Ghost:** Secondary uses raised graphite (`#141414`) with subtle border; ghost remains transparent with text emphasis on hover.

### Cards / Containers
- **Corner Style:** Large rounded shells (`24px`) for main content modules.
- **Background:** Graphite surface (`#0d0d0d`) with raised hover state (`#141414`).
- **Shadow Strategy:** Border-led separation with minimal shadow usage.
- **Border:** Quiet structural line (`#232323`).
- **Internal Padding:** Core modules use (`24px` to `32px`) spacing.

### Inputs / Fields
- **Style:** Raised dark field with border, large rounding (`16px`), fixed control height (`44px`).
- **Focus:** Border brightens and subtle ring appears for keyboard focus.
- **Error / Disabled:** Error switches to red border and ring context; disabled lowers opacity and interaction.

### Navigation
- **Desktop:** Pill-based nav inside a low-contrast container; active routes use white-tinted pill state.
- **Mobile:** Floating bottom capsule with blur and soft shadow; icons communicate core workflows at a glance.
- **State Language:** Active state is always filled, inactive state is muted text-on-transparent.

## 6. Do's and Don'ts

### Do:
- **Do** keep neutral surfaces dominant (`#050505`, `#0d0d0d`, `#141414`) and reserve teal for explicit action intent.
- **Do** use clear state feedback on controls: hover, focus-visible, and active must all be visually distinct.
- **Do** preserve compact hierarchy for operational scanning, especially in dashboard and plan flows.
- **Do** keep cards and modules function-led, with borders and tonal layering instead of decorative effects.

### Don't:
- **Don't** mimic generic motivational fitness apps that over-index on hype and streak pressure.
- **Don't** drift into clinical health dashboards that feel cold, bureaucratic, or hard to act on.
- **Don't** ship gamified interfaces that prioritize badges and novelty over training quality and adherence.
- **Don't** introduce over-designed "AI" aesthetics that reduce trust in recommendation quality.
- **Don't** use `border-left` or `border-right` accents greater than `1px` as visual decoration.
- **Don't** use gradient text, decorative glassmorphism defaults, or repetitive identical card grids.
