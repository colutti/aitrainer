# Landing Page Improvements Implementation Plan

> REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce spacing between landing page sections, add more Call to Action (CTA) buttons, and implement conversion rate optimization (CRO) improvements.

**Architecture:** 
- Reduce `py-24` and `py-20` standard padding across section containers (`TrainerShowcase`, `ProductShowcase`, `LandingPage`) to `py-12 md:py-16`.
- Add CTA buttons at the bottom of the `TrainerShowcase` and `ProductShowcase` sections to prompt users while they scroll.
- Add trust micro-copy (e.g., "Grátis para começar") near major CTAs for better client attraction.
- Ensure strict TypeScript typing and accurate translation keys in `react-i18next`.

**Tech Stack:** React, TailwindCSS v4, Vite, Vitest

---

### Task 1: Update Translation Files for new CTAs

**Files:**
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

**Step 1: Write the failing test**
(No direct test for translation JSONs, but we will add logic later. Skip failing test for JSON).

**Step 2: Write minimal implementation**
Add to `pt-BR.json` under `"landing"`:
```json
    "cta_trainers": "Escolha seu treinador agora",
    "cta_product": "Experimente o FityQ grátis",
    "trust_badge_free": "✓ Grátis para começar",
    "trust_badge_card": "✓ Sem cartão de crédito"
```
Do the same equivalent translated keys for `en-US.json` and `es-ES.json`.

**Step 3: Commit**
```bash
git add frontend/src/locales/
git commit -m "feat: add translation keys for new landing page CTAs"
```

---

### Task 2: Reduce spacing and add CTA in TrainerShowcase

**Files:**
- Modify: `frontend/src/features/landing/TrainerShowcase.tsx`

**Step 1: Write the failing test**
In an existing or new test for `TrainerShowcase`, assert the presence of the new CTA button.
(Assume we have frontend container tests, or we can simply verify visually through component).

**Step 2: Write minimal implementation**
1. Change `<section id="treinadores" className="py-24 px-4 sm:px-6 lg:px-8">` to `<section id="treinadores" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">`.
2. At the bottom of the section (just before `</section>`), add a centered CTA:
```tsx
        {/* Call to Action for Trainers */}
        <div className="mt-12 flex justify-center">
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="primary"
            size="lg"
            className="shadow-md shadow-primary/20 group animate-pulse-glow"
          >
            {t('landing.cta_trainers')}
          </Button>
        </div>
```

**Step 3: Run linter to verify**
Run: `cd frontend && npm run lint`
Expected: PASS with 0 warnings/errors.

**Step 4: Commit**
```bash
git add frontend/src/features/landing/TrainerShowcase.tsx
git commit -m "style: reduce padding and add cta to trainer showcase"
```

---

### Task 3: Reduce spacing and add CTA in ProductShowcase

**Files:**
- Modify: `frontend/src/features/landing/ProductShowcase.tsx`

**Step 1: Write minimal implementation**
1. Change `<section className="py-20 px-4 sm:px-6 lg:px-8">` to `<section className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">`.
2. Adjust `import { useNavigate } from 'react-router-dom';` and `import { Button } from '@shared/components/ui/Button';` at the top.
3. Add `const navigate = useNavigate();` inside the component.
4. At the bottom of the section before `</section>`, add:
```tsx
        {/* Call to Action for Product */}
        <div className="mt-12 flex justify-center">
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="primary"
            size="lg"
            className="shadow-md shadow-primary/20"
          >
            {t('landing.cta_product')}
          </Button>
        </div>
```

**Step 2: Run linter to verify**
Run: `cd frontend && npm run check`
Expected: PASS with 0 warnings/errors.

**Step 3: Commit**
```bash
git add frontend/src/features/landing/ProductShowcase.tsx
git commit -m "style: reduce padding and add cta to product showcase"
```

---

### Task 4: Reduce overall spacing and add Trust Badges in LandingPage

**Files:**
- Modify: `frontend/src/features/landing/LandingPage.tsx`

**Step 1: Write minimal implementation**
1. Change padding on remaining sections:
   - `Hero Section`: update layout if needed.
   - `Diferenciais Section`: `<section id="diferenciais" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 relative z-10">`
   - `Como Funciona Section`: `<section id="como-funciona" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 relative z-10">`
   - `Planos Section`: `<section id="planos" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">`
2. Add Trust Badges near Hero CTA:
   Find the Hero buttons div and add below it:
```tsx
            <div className="mt-4 flex flex-wrap gap-4 text-xs text-text-secondary">
              <span className="flex items-center gap-1">
                {t('landing.trust_badge_free')}
              </span>
              <span className="flex items-center gap-1">
                 {t('landing.trust_badge_card')}
              </span>
            </div>
```
3. Add same Trust Badges near Final CTA.

**Step 2: Run linter & typescript to verify**
Run: `cd frontend && npm run check`
Expected: PASS with 0 warnings/errors.

**Step 3: Commit**
```bash
git add frontend/src/features/landing/LandingPage.tsx
git commit -m "style: refine landing page spacing and add trust badges"
```
