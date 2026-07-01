---
name: FityQ Performance Coaching Interface
description: Dark-first design system for a high-clarity fitness coaching product.
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#1f1f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#303030'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb786'
  on-tertiary: '#502400'
  tertiary-container: '#df7412'
  on-tertiary-container: '#461f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  background: '#131313'
  on-background: '#e2e2e2'
  surface-variant: '#353535'
typography:
  hero-display:
    fontFamily: Inter
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  card-title:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0em
  label-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-page: 40px
  card-padding: 24px
---

# Design System: FityQ Performance Coaching Interface

## 1. Intent

FityQ is a coaching product, not a developer tool. The interface should feel focused, confident, and operational: users come to understand what to do next, not to admire decoration. The current visual system is dark-first, dense enough for dashboards and plans, and restrained enough to keep the AI experience trustworthy.

## 2. Visual language

- Dark surfaces with clear tonal steps separate content without relying on heavy shadow.
- Blue is the primary action color.
- Green and orange communicate positive/supporting states and warnings.
- High-contrast typography carries hierarchy more than illustration or ornament.

The design should feel precise and modern, but still human. It supports training, nutrition, body metrics, and coaching conversations rather than generic “AI” spectacle.

## 3. Tokens

The canonical frontend tokens live in `frontend/src/index.css` and the semantic variants live in `frontend/src/shared/styles/ui-variants.ts`.

Core traits:

- Base background: `#131313`
- Main card surface: `surface-container`
- Main border: `outline-variant`
- Primary action: `primary`
- Success/accent: `secondary`
- Warning/accent: `tertiary`

## 4. Typography

Inter is used across the system.

- Large headings establish page-level orientation.
- Label text is compact, uppercase, and slightly tracked.
- Body text stays readable for longer coaching explanations, logs, and tables.
- Numeric summaries should read as strong signals, not decorative counters.

## 5. Layout and components

Current reusable primitives:

- `PremiumCard`
- `ViewHeader`
- `FormField`
- `PREMIUM_UI` button, text, badge, grid, and card variants

Layout rules:

- Preserve a centered content width around `1280px`.
- Favor stacked sections with clear spacing over overloaded mega-panels.
- Use bento-style stat layouts where they improve scanability, not by default everywhere.

## 6. Interaction rules

- Motion should be subtle and brief.
- Hover states should clarify affordance, not restyle the whole page.
- Focus states must stay obvious against dark surfaces.
- User-facing status, errors, and progress should never rely on color alone.

## 7. Avoid

- Developer-tool framing in copy or visual rationale.
- Decorative glow, glass excess, or gratuitous gradients.
- Mixing unrelated layout grammars between equivalent screens.
- Introducing one-off tokens instead of extending the shared token system.
