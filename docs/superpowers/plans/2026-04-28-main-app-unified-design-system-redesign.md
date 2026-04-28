# Main App Unified Design System Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign every main-app screen in `frontend/` so public, onboarding, and authenticated surfaces all use one centralized dark product design system with shared templates for equivalent tasks.

**Architecture:** Replace the visual foundation first, then enforce consistency through shared primitives and screen templates instead of screen-local styling. Migrate consumers by surface group so forms, lists, insights, chat, and settings all converge on the same structural grammar while preserving current behavior and route coverage.

**Tech Stack:** React 19, TypeScript 5.9, React Router 7, TailwindCSS v4, Zustand, Vitest, Testing Library, i18next

---

### Task 1: Replace The Global Token Foundation

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/shared/styles/ui-variants.ts`
- Test: `frontend/src/shared/components/ui/Button.test.tsx`
- Test: `frontend/src/shared/components/ui/Input.test.tsx`
- Test: `frontend/src/shared/components/ui/premium/PremiumCard.test.tsx`

- [ ] **Step 1: Write failing tests for the new shared token language**

```tsx
it('renders primary buttons with the design-system token classes', () => {
  render(<Button>Salvar</Button>);

  expect(screen.getByRole('button', { name: 'Salvar' })).toHaveClass('bg-[color:var(--color-primary)]');
});

it('renders inputs with the shared field surface classes', () => {
  render(<Input aria-label="Nome" />);

  expect(screen.getByLabelText('Nome')).toHaveClass('border-[color:var(--color-outline-variant)]');
  expect(screen.getByLabelText('Nome')).toHaveClass('bg-[color:var(--color-surface-container-low)]');
});

it('renders cards with the shared surface classes', () => {
  render(<PremiumCard data-testid="card">content</PremiumCard>);

  expect(screen.getByTestId('card')).toHaveClass('bg-[color:var(--color-surface-container)]');
  expect(screen.getByTestId('card')).toHaveClass('border-[color:var(--color-outline-variant)]');
});
```

- [ ] **Step 2: Run the focused component tests to confirm the foundation is still old**

Run: `cd frontend && npm test -- src/shared/components/ui/Button.test.tsx src/shared/components/ui/Input.test.tsx src/shared/components/ui/premium/PremiumCard.test.tsx`
Expected: FAIL because the current tokens still use the older monochrome-teal foundation and mismatched utility classes.

- [ ] **Step 3: Replace the CSS tokens and semantic utility roles in the global theme**

```css
@theme {
  --font-display: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;

  --color-background: #131313;
  --color-on-background: #e2e2e2;
  --color-surface: #131313;
  --color-surface-container-lowest: #0e0e0e;
  --color-surface-container-low: #1b1b1b;
  --color-surface-container: #1f1f1f;
  --color-surface-container-high: #2a2a2a;
  --color-surface-container-highest: #353535;
  --color-surface-variant: #353535;
  --color-on-surface: #e2e2e2;
  --color-on-surface-variant: #c2c6d6;
  --color-outline: #8c909f;
  --color-outline-variant: #424754;
  --color-primary: #adc6ff;
  --color-on-primary: #002e6a;
  --color-primary-container: #4d8eff;
  --color-secondary: #4edea3;
  --color-on-secondary: #003824;
  --color-tertiary: #ffb786;
  --color-on-tertiary: #502400;
  --color-error: #ffb4ab;
  --color-on-error: #690005;

  --space-base: 8px;
  --space-gutter: 24px;
  --space-page: 40px;
  --space-card: 24px;
  --radius-sm: 2px;
  --radius-default: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --container-max: 1280px;
}

@utility app-surface {
  @apply border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] text-[color:var(--color-on-surface)];
}

@utility app-field {
  @apply h-11 rounded-[var(--radius-md)] border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] text-[color:var(--color-on-surface)] placeholder:text-[color:var(--color-on-surface-variant)] focus-visible:border-[color:var(--color-primary)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-primary)]/20;
}
```

```ts
export const PREMIUM_UI = {
  pageWrapper:
    'min-h-screen bg-[color:var(--color-background)] text-[color:var(--color-on-background)] font-sans',
  page: 'mx-auto w-full max-w-[var(--container-max)] px-4 md:px-6 xl:px-[var(--space-gutter)]',
  section: 'space-y-6',
  card: {
    base: 'app-surface rounded-[var(--radius-lg)]',
    hover: 'hover:bg-[color:var(--color-surface-container-high)] transition-colors duration-200',
    padding: 'p-6',
  },
  text: {
    label: 'text-[13px] font-medium uppercase tracking-[0.05em] text-[color:var(--color-on-surface-variant)]',
    heading: 'text-[32px] font-semibold tracking-[-0.01em] text-[color:var(--color-on-surface)]',
    title: 'text-[18px] font-semibold text-[color:var(--color-on-surface)]',
    body: 'text-[16px] leading-[1.6] text-[color:var(--color-on-surface-variant)]',
  },
};
```

- [ ] **Step 4: Re-run the focused component tests**

Run: `cd frontend && npm test -- src/shared/components/ui/Button.test.tsx src/shared/components/ui/Input.test.tsx src/shared/components/ui/premium/PremiumCard.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate for the foundation**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the global design foundation**

```bash
git add frontend/src/index.css frontend/src/shared/styles/ui-variants.ts frontend/src/shared/components/ui/Button.test.tsx frontend/src/shared/components/ui/Input.test.tsx frontend/src/shared/components/ui/premium/PremiumCard.test.tsx
git commit -m "feat: replace main app design tokens and utility foundation"
```

### Task 2: Refactor Shared Controls Into System Primitives

**Files:**
- Modify: `frontend/src/shared/components/ui/Button.tsx`
- Modify: `frontend/src/shared/components/ui/Button.test.tsx`
- Modify: `frontend/src/shared/components/ui/Input.tsx`
- Modify: `frontend/src/shared/components/ui/Input.test.tsx`
- Modify: `frontend/src/shared/components/ui/DateInput.tsx`
- Modify: `frontend/src/shared/components/ui/DateInput.test.tsx`
- Modify: `frontend/src/shared/components/ui/EmptyState.tsx`
- Modify: `frontend/src/shared/components/ui/EmptyState.test.tsx`
- Modify: `frontend/src/shared/components/ui/Pagination.tsx`
- Modify: `frontend/src/shared/components/ui/Pagination.test.tsx`
- Modify: `frontend/src/shared/components/ui/Toast.tsx`
- Modify: `frontend/src/shared/components/ui/ToastContainer.tsx`
- Modify: `frontend/src/shared/components/ui/GlobalErrorBoundary.tsx`
- Modify: `frontend/src/shared/components/ui/premium/PremiumCard.tsx`
- Modify: `frontend/src/shared/components/ui/premium/PremiumDrawer.tsx`
- Modify: `frontend/src/shared/components/ui/premium/FormField.tsx`
- Modify: `frontend/src/shared/components/ui/premium/ViewHeader.tsx`

- [ ] **Step 1: Add failing tests for consistent states across shared controls**

```tsx
it('keeps primary, secondary, ghost, and danger buttons inside one visual vocabulary', () => {
  const { rerender } = render(<Button variant="primary">Primary</Button>);
  expect(screen.getByRole('button', { name: 'Primary' })).toHaveClass('rounded-[var(--radius-md)]');

  rerender(<Button variant="secondary">Secondary</Button>);
  expect(screen.getByRole('button', { name: 'Secondary' })).toHaveClass('border-[color:var(--color-outline-variant)]');

  rerender(<Button variant="ghost">Ghost</Button>);
  expect(screen.getByRole('button', { name: 'Ghost' })).toHaveClass('bg-transparent');
});

it('renders inline field labels and error copy with the shared field rhythm', () => {
  render(<Input id="weight" label="Peso" error="Obrigatorio" />);

  expect(screen.getByText('Peso')).toHaveClass('text-[13px]');
  expect(screen.getByText('Obrigatorio')).toHaveClass('text-[color:var(--color-error)]');
});
```

- [ ] **Step 2: Run the focused shared-control tests**

Run: `cd frontend && npm test -- src/shared/components/ui/Button.test.tsx src/shared/components/ui/Input.test.tsx src/shared/components/ui/DateInput.test.tsx src/shared/components/ui/EmptyState.test.tsx src/shared/components/ui/Pagination.test.tsx`
Expected: FAIL because the current controls still expose mixed radius, hover, blur, and label conventions.

- [ ] **Step 3: Refactor the shared controls to own the new default system styling**

```tsx
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] text-sm font-semibold transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--color-primary)]/25 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-[color:var(--color-primary)] text-[color:var(--color-on-primary)] hover:bg-[color:var(--color-primary-container)]',
        secondary: 'border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] text-[color:var(--color-on-surface)] hover:bg-[color:var(--color-surface-container-high)]',
        ghost: 'bg-transparent text-[color:var(--color-on-surface)] hover:bg-[color:var(--color-surface-container-low)]',
        danger: 'border border-[color:var(--color-error)]/30 bg-[color:var(--color-error)]/10 text-[color:var(--color-error)] hover:bg-[color:var(--color-error)]/15',
      },
    },
  }
);
```

```tsx
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, leftIcon, className, ...props }, ref) => (
    <div className="space-y-2">
      {label ? <label htmlFor={props.id} className="text-[13px] font-medium text-[color:var(--color-on-surface-variant)]">{label}</label> : null}
      <div className="relative">
        {leftIcon ? <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[color:var(--color-on-surface-variant)]">{leftIcon}</span> : null}
        <input ref={ref} className={cn('app-field w-full px-3 text-sm', leftIcon && 'pl-10', error && 'border-[color:var(--color-error)] focus-visible:ring-[color:var(--color-error)]/20', className)} {...props} />
      </div>
      {error ? <p className="text-sm text-[color:var(--color-error)]">{error}</p> : null}
    </div>
  )
);
```

- [ ] **Step 4: Re-run the focused shared-control tests**

Run: `cd frontend && npm test -- src/shared/components/ui/Button.test.tsx src/shared/components/ui/Input.test.tsx src/shared/components/ui/DateInput.test.tsx src/shared/components/ui/EmptyState.test.tsx src/shared/components/ui/Pagination.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the shared validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the primitive-control refactor**

```bash
git add frontend/src/shared/components/ui/Button.tsx frontend/src/shared/components/ui/Button.test.tsx frontend/src/shared/components/ui/Input.tsx frontend/src/shared/components/ui/Input.test.tsx frontend/src/shared/components/ui/DateInput.tsx frontend/src/shared/components/ui/DateInput.test.tsx frontend/src/shared/components/ui/EmptyState.tsx frontend/src/shared/components/ui/EmptyState.test.tsx frontend/src/shared/components/ui/Pagination.tsx frontend/src/shared/components/ui/Pagination.test.tsx frontend/src/shared/components/ui/Toast.tsx frontend/src/shared/components/ui/ToastContainer.tsx frontend/src/shared/components/ui/GlobalErrorBoundary.tsx frontend/src/shared/components/ui/premium/PremiumCard.tsx frontend/src/shared/components/ui/premium/PremiumDrawer.tsx frontend/src/shared/components/ui/premium/FormField.tsx frontend/src/shared/components/ui/premium/ViewHeader.tsx
git commit -m "feat: refactor shared ui controls into unified design primitives"
```

### Task 3: Add Shared Screen Templates And Layout Building Blocks

**Files:**
- Create: `frontend/src/shared/components/layout/AppShell.tsx`
- Create: `frontend/src/shared/components/layout/PageHeader.tsx`
- Create: `frontend/src/shared/components/layout/ScreenSection.tsx`
- Create: `frontend/src/shared/components/layout/EntityFormScreen.tsx`
- Create: `frontend/src/shared/components/layout/EntityListScreen.tsx`
- Create: `frontend/src/shared/components/layout/InsightScreen.tsx`
- Create: `frontend/src/shared/components/layout/StickyActionBar.tsx`
- Create: `frontend/src/shared/components/layout/ListToolbar.tsx`
- Create: `frontend/src/shared/components/layout/StatusChip.tsx`
- Create: `frontend/src/shared/components/layout/layoutModes.ts`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.tsx`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`
- Test: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`

- [ ] **Step 1: Add failing tests for the new shared shell and template hooks**

```tsx
it('renders the desktop shell inside the centralized content container', () => {
  render(
    <MemoryRouter initialEntries={['/dashboard/workouts']}>
      <PremiumLayout />
    </MemoryRouter>
  );

  expect(screen.getByTestId('app-shell-main')).toHaveClass('max-w-[1280px]');
  expect(screen.getByTestId('desktop-nav')).toHaveClass('border-[color:var(--color-outline-variant)]');
});

it('exposes a reusable page header contract for feature screens', () => {
  render(
    <PageHeader
      eyebrow="Treinos"
      title="Biblioteca de treinos"
      description="Consulte, filtre e crie treinos no mesmo padrao visual."
    />
  );

  expect(screen.getByText('Treinos')).toHaveClass('text-[13px]');
  expect(screen.getByText('Biblioteca de treinos')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the shell and template tests**

Run: `cd frontend && npm test -- src/shared/components/layout/PremiumLayout.test.tsx`
Expected: FAIL because the centralized screen-template primitives do not exist yet.

- [ ] **Step 3: Implement the shell and screen-template layer**

```tsx
export function EntityListScreen({
  header,
  toolbar,
  children,
}: {
  header: React.ReactNode;
  toolbar?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-6">
      {header}
      {toolbar ? <div className="app-surface rounded-[var(--radius-lg)] p-4">{toolbar}</div> : null}
      <div className="space-y-4">{children}</div>
    </section>
  );
}
```

```tsx
export function EntityFormScreen({
  header,
  sections,
  actions,
}: {
  header: React.ReactNode;
  sections: React.ReactNode;
  actions: React.ReactNode;
}) {
  return (
    <section className="space-y-6">
      {header}
      <div className="space-y-4">{sections}</div>
      <StickyActionBar>{actions}</StickyActionBar>
    </section>
  );
}
```

```tsx
<main className="pb-32 pt-4 md:pt-24 min-h-0 flex-1 overflow-y-auto">
  <div data-testid="app-shell-main" className={cn('mx-auto w-full px-4 md:px-6 xl:px-[var(--space-gutter)]', layoutMode.contentClassName)}>
    <Outlet />
  </div>
</main>
```

- [ ] **Step 4: Re-run the shell and layout tests**

Run: `cd frontend && npm test -- src/shared/components/layout/PremiumLayout.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the layout/template layer**

```bash
git add frontend/src/shared/components/layout/AppShell.tsx frontend/src/shared/components/layout/PageHeader.tsx frontend/src/shared/components/layout/ScreenSection.tsx frontend/src/shared/components/layout/EntityFormScreen.tsx frontend/src/shared/components/layout/EntityListScreen.tsx frontend/src/shared/components/layout/InsightScreen.tsx frontend/src/shared/components/layout/StickyActionBar.tsx frontend/src/shared/components/layout/ListToolbar.tsx frontend/src/shared/components/layout/StatusChip.tsx frontend/src/shared/components/layout/layoutModes.ts frontend/src/shared/components/layout/PremiumLayout.tsx frontend/src/shared/components/layout/PremiumLayout.test.tsx
git commit -m "feat: add unified app shell and shared screen templates"
```

### Task 4: Migrate Public Surfaces And Route Entrypoints

**Files:**
- Modify: `frontend/src/AppRoutes.tsx`
- Modify: `frontend/src/features/landing/LandingPage.tsx`
- Modify: `frontend/src/features/landing/components/Navbar.tsx`
- Modify: `frontend/src/features/landing/components/Hero.tsx`
- Modify: `frontend/src/features/landing/components/Features.tsx`
- Modify: `frontend/src/features/landing/components/HowItWorks.tsx`
- Modify: `frontend/src/features/landing/components/ComparisonTable.tsx`
- Modify: `frontend/src/features/landing/components/ProductShowcase.tsx`
- Modify: `frontend/src/features/landing/components/TrainerShowcase.tsx`
- Modify: `frontend/src/features/landing/components/ChatCarousel.tsx`
- Modify: `frontend/src/features/landing/components/Counters.tsx`
- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/landing/components/FAQ.tsx`
- Modify: `frontend/src/features/landing/components/FinalCTA.tsx`
- Modify: `frontend/src/features/landing/components/Footer.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.tsx`
- Modify: `frontend/src/features/landing/components/StickyMobileCTA.tsx`
- Modify: `frontend/src/features/auth/LoginPage.tsx`
- Modify: `frontend/src/features/auth/ResetPasswordPage.tsx`
- Modify: `frontend/src/features/legal/TermsPage.tsx`
- Modify: `frontend/src/features/legal/PrivacyPage.tsx`
- Modify: `frontend/src/features/landing/LandingPage.test.tsx`
- Modify: `frontend/src/features/auth/LoginPage.test.tsx`
- Modify: `frontend/src/features/auth/ResetPasswordPage.test.tsx`
- Test: `frontend/src/AppRoutes.test.tsx`

- [ ] **Step 1: Add failing route-level smoke tests for the public design migration**

```tsx
it('keeps the landing route inside the new public surface language', () => {
  render(<AppRoutes />, { route: '/' });
  expect(screen.getByTestId('landing-shell')).toHaveClass('bg-[color:var(--color-background)]');
});

it('renders login inside the unified form structure', () => {
  render(<AppRoutes />, { route: '/login' });
  expect(screen.getByTestId('auth-form-shell')).toBeInTheDocument();
});

it('renders legal pages inside the shared content container', () => {
  render(<AppRoutes />, { route: '/termos-de-uso' });
  expect(screen.getByTestId('legal-page-shell')).toHaveClass('max-w-[1280px]');
});
```

- [ ] **Step 2: Run the public-surface tests**

Run: `cd frontend && npm test -- src/AppRoutes.test.tsx src/features/landing/LandingPage.test.tsx src/features/auth/LoginPage.test.tsx src/features/auth/ResetPasswordPage.test.tsx`
Expected: FAIL because the public screens still use older styling and lack the shared test markers.

- [ ] **Step 3: Redesign all public screens with the same token system and structural patterns**

```tsx
<main data-testid="auth-form-shell" className="min-h-screen bg-[color:var(--color-background)] text-[color:var(--color-on-background)]">
  <div className="mx-auto flex min-h-screen w-full max-w-[1280px] items-center px-4 py-10 md:px-6">
    <section className="w-full max-w-[480px] app-surface rounded-[var(--radius-lg)] p-6 md:p-8">
      <PageHeader eyebrow={t('auth.eyebrow')} title={t('auth.title')} description={t('auth.subtitle')} />
      {formContent}
    </section>
  </div>
</main>
```

```tsx
<article data-testid="legal-page-shell" className="mx-auto max-w-[1280px] px-4 py-10 md:px-6">
  <PageHeader title={t('legal.terms.title')} description={t('legal.terms.updatedAt')} />
  <div className="app-surface rounded-[var(--radius-lg)] p-6 md:p-8">{content}</div>
</article>
```

- [ ] **Step 4: Re-run the public-surface tests**

Run: `cd frontend && npm test -- src/AppRoutes.test.tsx src/features/landing/LandingPage.test.tsx src/features/auth/LoginPage.test.tsx src/features/auth/ResetPasswordPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the public-surface migration**

```bash
git add frontend/src/AppRoutes.tsx frontend/src/features/landing frontend/src/features/auth/LoginPage.tsx frontend/src/features/auth/ResetPasswordPage.tsx frontend/src/features/legal/TermsPage.tsx frontend/src/features/legal/PrivacyPage.tsx frontend/src/features/landing/LandingPage.test.tsx frontend/src/features/auth/LoginPage.test.tsx frontend/src/features/auth/ResetPasswordPage.test.tsx frontend/src/AppRoutes.test.tsx
git commit -m "feat: migrate public main-app screens to unified design system"
```

### Task 5: Migrate Onboarding, Dashboard, And Plan Insight Screens

**Files:**
- Modify: `frontend/src/features/onboarding/components/OnboardingPage.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingPage.test.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.test.tsx`
- Modify: `frontend/src/features/dashboard/DashboardPage.tsx`
- Modify: `frontend/src/features/dashboard/DashboardPage.test.tsx`
- Modify: `frontend/src/features/dashboard/components/DashboardView.tsx`
- Modify: `frontend/src/features/dashboard/components/DashboardWorkspaceSection.tsx`
- Modify: `frontend/src/features/plan/PlanPage.tsx`
- Modify: `frontend/src/features/plan/PlanPage.test.tsx`
- Modify: `frontend/src/features/plan/components/PlanView.tsx`
- Modify: `frontend/src/features/plan/components/PlanView.test.tsx`

- [ ] **Step 1: Add failing tests for the shared insight-screen grammar**

```tsx
it('renders onboarding inside the shared stepped-flow sections', () => {
  render(<OnboardingPage />);
  expect(screen.getByTestId('onboarding-screen')).toBeInTheDocument();
  expect(screen.getByTestId('onboarding-screen')).toHaveClass('space-y-6');
});

it('renders dashboard inside the shared insight screen container', () => {
  render(<DashboardPage />);
  expect(screen.getByTestId('dashboard-insight-screen')).toBeInTheDocument();
});

it('renders the plan screen using the same page header and section rhythm', () => {
  render(<PlanPage />);
  expect(screen.getByTestId('plan-screen')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the onboarding, dashboard, and plan tests**

Run: `cd frontend && npm test -- src/features/onboarding/components/OnboardingPage.test.tsx src/features/onboarding/components/OnboardingView.test.tsx src/features/dashboard/DashboardPage.test.tsx src/features/plan/PlanPage.test.tsx src/features/plan/components/PlanView.test.tsx`
Expected: FAIL because these screens still have bespoke layout structures and older visual helpers.

- [ ] **Step 3: Migrate onboarding, dashboard, and plan onto shared section and insight templates**

```tsx
return (
  <InsightScreen
    data-testid="dashboard-insight-screen"
    header={
      <PageHeader
        eyebrow={t('dashboard.eyebrow')}
        title={t('dashboard.title')}
        description={t('dashboard.subtitle')}
      />
    }
  >
    <ScreenSection title={t('dashboard.sections.overview')}>
      {overviewContent}
    </ScreenSection>
    <ScreenSection title={t('dashboard.sections.trends')}>
      {trendContent}
    </ScreenSection>
  </InsightScreen>
);
```

```tsx
return (
  <div data-testid="onboarding-screen" className="space-y-6">
    <PageHeader eyebrow={stepEyebrow} title={stepTitle} description={stepDescription} />
    <FormSection>{stepFields}</FormSection>
    <StickyActionBar>{stepActions}</StickyActionBar>
  </div>
);
```

- [ ] **Step 4: Re-run the onboarding, dashboard, and plan tests**

Run: `cd frontend && npm test -- src/features/onboarding/components/OnboardingPage.test.tsx src/features/onboarding/components/OnboardingView.test.tsx src/features/dashboard/DashboardPage.test.tsx src/features/plan/PlanPage.test.tsx src/features/plan/components/PlanView.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the insight-screen migration**

```bash
git add frontend/src/features/onboarding/components/OnboardingPage.tsx frontend/src/features/onboarding/components/OnboardingView.tsx frontend/src/features/onboarding/components/OnboardingPage.test.tsx frontend/src/features/onboarding/components/OnboardingView.test.tsx frontend/src/features/dashboard/DashboardPage.tsx frontend/src/features/dashboard/DashboardPage.test.tsx frontend/src/features/dashboard/components/DashboardView.tsx frontend/src/features/dashboard/components/DashboardWorkspaceSection.tsx frontend/src/features/plan/PlanPage.tsx frontend/src/features/plan/PlanPage.test.tsx frontend/src/features/plan/components/PlanView.tsx frontend/src/features/plan/components/PlanView.test.tsx
git commit -m "feat: migrate onboarding dashboard and plan to unified insight templates"
```

### Task 6: Migrate Workout, Nutrition, And Body Flows To Shared Form/List Templates

**Files:**
- Modify: `frontend/src/features/workouts/WorkoutsPage.tsx`
- Modify: `frontend/src/features/workouts/WorkoutsPage.test.tsx`
- Modify: `frontend/src/features/workouts/components/WorkoutsView.tsx`
- Modify: `frontend/src/features/workouts/components/WorkoutCard.tsx`
- Modify: `frontend/src/features/workouts/components/WorkoutDrawer.tsx`
- Modify: `frontend/src/features/nutrition/NutritionPage.tsx`
- Modify: `frontend/src/features/nutrition/NutritionPage.test.tsx`
- Modify: `frontend/src/features/nutrition/components/NutritionView.tsx`
- Modify: `frontend/src/features/nutrition/components/NutritionLogCard.tsx`
- Modify: `frontend/src/features/body/BodyPage.tsx`
- Modify: `frontend/src/features/body/BodyPage.test.tsx`
- Modify: `frontend/src/features/body/NutritionPage.tsx`
- Modify: `frontend/src/features/body/components/BodyView.tsx`
- Modify: `frontend/src/features/body/components/WeightTab.tsx`
- Modify: `frontend/src/features/body/components/WeightLogCard.tsx`
- Modify: `frontend/src/features/body/components/WeightLogDrawer.tsx`
- Modify: `frontend/src/features/body/components/NutritionTab.tsx`
- Modify: `frontend/src/features/body/components/NutritionLogDrawer.tsx`
- Modify: `frontend/src/features/body/components/NutritionLogDrawer.test.tsx`
- Modify: `frontend/src/features/body/components/WeightLogDrawer.test.tsx`
- Modify: `frontend/src/features/body/components/WeightTab.test.tsx`
- Modify: `frontend/src/features/body/components/NutritionTab.test.tsx`

- [ ] **Step 1: Add failing tests that assert shared patterns across equivalent domain flows**

```tsx
it('renders workout listing through the entity list screen contract', () => {
  render(<WorkoutsPage />);
  expect(screen.getByTestId('workouts-list-screen')).toBeInTheDocument();
});

it('renders nutrition listing through the same list-screen contract', () => {
  render(<NutritionPage />);
  expect(screen.getByTestId('nutrition-list-screen')).toBeInTheDocument();
});

it('renders body log creation through the shared entity form contract', () => {
  render(<WeightLogDrawer isOpen onClose={vi.fn()} />);
  expect(screen.getByTestId('entity-form-screen')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the focused domain-flow tests**

Run: `cd frontend && npm test -- src/features/workouts/WorkoutsPage.test.tsx src/features/nutrition/NutritionPage.test.tsx src/features/body/BodyPage.test.tsx src/features/body/components/WeightLogDrawer.test.tsx src/features/body/components/NutritionLogDrawer.test.tsx src/features/body/components/WeightTab.test.tsx src/features/body/components/NutritionTab.test.tsx`
Expected: FAIL because equivalent screens still use independent layout structures.

- [ ] **Step 3: Refactor workouts, nutrition, and body flows onto the shared list and form templates**

```tsx
return (
  <EntityListScreen
    header={<PageHeader eyebrow={t('workouts.eyebrow')} title={t('workouts.title')} description={t('workouts.subtitle')} />}
    toolbar={<ListToolbar search={searchControl} actions={primaryActions} filters={filterControls} />}
  >
    {items.map((workout) => (
      <ListItemRow key={workout.id}>{renderWorkout(workout)}</ListItemRow>
    ))}
  </EntityListScreen>
);
```

```tsx
return (
  <EntityFormScreen
    header={<PageHeader eyebrow={t('body.log.eyebrow')} title={t('body.log.title')} description={t('body.log.subtitle')} />}
    sections={
      <>
        <FormSection title={t('body.log.sections.metrics')}>{metricFields}</FormSection>
        <FormSection title={t('body.log.sections.notes')}>{noteFields}</FormSection>
      </>
    }
    actions={drawerActions}
  />
);
```

- [ ] **Step 4: Re-run the focused domain-flow tests**

Run: `cd frontend && npm test -- src/features/workouts/WorkoutsPage.test.tsx src/features/nutrition/NutritionPage.test.tsx src/features/body/BodyPage.test.tsx src/features/body/components/WeightLogDrawer.test.tsx src/features/body/components/NutritionLogDrawer.test.tsx src/features/body/components/WeightTab.test.tsx src/features/body/components/NutritionTab.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the workout, nutrition, and body migration**

```bash
git add frontend/src/features/workouts frontend/src/features/nutrition frontend/src/features/body
git commit -m "feat: unify workout nutrition and body screens under shared templates"
```

### Task 7: Migrate Chat And Memory/Settings Surfaces To The Unified System

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.test.tsx`
- Modify: `frontend/src/features/chat/components/ChatContextPanel.tsx`
- Modify: `frontend/src/features/chat/components/MessageBubble.tsx`
- Modify: `frontend/src/features/chat/components/MessageBubble.test.tsx`
- Modify: `frontend/src/features/memories/MemoriesPage.tsx`
- Modify: `frontend/src/features/memories/MemoriesPage.test.tsx`
- Modify: `frontend/src/features/memories/components/MemoriesView.tsx`
- Modify: `frontend/src/features/memories/components/MemoriesView.test.tsx`
- Modify: `frontend/src/features/settings/SettingsPage.tsx`
- Modify: `frontend/src/features/settings/SettingsPage.test.tsx`
- Modify: `frontend/src/features/settings/components/UserProfilePage.tsx`
- Modify: `frontend/src/features/settings/components/UserProfileView.tsx`
- Modify: `frontend/src/features/settings/components/UserProfileView.test.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionView.tsx`
- Modify: `frontend/src/features/settings/components/TrainerSettingsPage.tsx`
- Modify: `frontend/src/features/settings/components/TrainerSettingsView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsPage.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.test.tsx`
- Modify: `frontend/src/features/settings/components/PhotoUpload.tsx`

- [ ] **Step 1: Add failing tests for conversation and settings consistency**

```tsx
it('renders chat inside the conversation screen shell', () => {
  render(<ChatPage />);
  expect(screen.getByTestId('conversation-screen')).toBeInTheDocument();
});

it('renders memories as a list screen inside settings vocabulary', () => {
  render(<MemoriesPage />);
  expect(screen.getByTestId('memories-list-screen')).toBeInTheDocument();
});

it('renders profile settings with the same form section grammar as other entity forms', () => {
  render(<UserProfilePage />);
  expect(screen.getByTestId('profile-form-screen')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the chat and settings tests**

Run: `cd frontend && npm test -- src/features/chat/ChatPage.test.tsx src/features/chat/components/ChatView.test.tsx src/features/chat/components/MessageBubble.test.tsx src/features/memories/MemoriesPage.test.tsx src/features/memories/components/MemoriesView.test.tsx src/features/settings/SettingsPage.test.tsx src/features/settings/components/UserProfileView.test.tsx src/features/settings/components/SubscriptionView.test.tsx src/features/settings/components/TrainerSettingsView.test.tsx src/features/settings/components/IntegrationsView.test.tsx`
Expected: FAIL because these surfaces still mix bespoke shells and older card/button language.

- [ ] **Step 3: Refactor chat, memories, and settings routes onto the unified shell contracts**

```tsx
return (
  <section data-testid="conversation-screen" className="grid min-h-[calc(100dvh-9rem)] gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
    <div className="app-surface rounded-[var(--radius-lg)]">{chatThread}</div>
    <aside className="space-y-4">
      <SurfaceCard>{contextPanel}</SurfaceCard>
      <SurfaceCard>{quickActions}</SurfaceCard>
    </aside>
  </section>
);
```

```tsx
return (
  <EntityFormScreen
    header={<PageHeader eyebrow={t('settings.profile.eyebrow')} title={t('settings.profile.title')} description={t('settings.profile.subtitle')} />}
    sections={<>{profileFields}{avatarUploadBlock}</>}
    actions={profileActions}
  />
);
```

- [ ] **Step 4: Re-run the chat and settings tests**

Run: `cd frontend && npm test -- src/features/chat/ChatPage.test.tsx src/features/chat/components/ChatView.test.tsx src/features/chat/components/MessageBubble.test.tsx src/features/memories/MemoriesPage.test.tsx src/features/memories/components/MemoriesView.test.tsx src/features/settings/SettingsPage.test.tsx src/features/settings/components/UserProfileView.test.tsx src/features/settings/components/SubscriptionView.test.tsx src/features/settings/components/TrainerSettingsView.test.tsx src/features/settings/components/IntegrationsView.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the chat and settings migration**

```bash
git add frontend/src/features/chat frontend/src/features/memories frontend/src/features/settings
git commit -m "feat: migrate chat memories and settings to unified design system"
```

### Task 8: Remove Legacy Styling Residue And Update Copy Across All Locales

**Files:**
- Modify: `frontend/src/shared/components/plans/PlanCard.tsx`
- Modify: `frontend/src/shared/components/plans/PlanCard.test.tsx`
- Modify: `frontend/src/shared/components/ui/LanguageSelector.tsx`
- Modify: `frontend/src/shared/components/ui/LanguageSelector.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`
- Modify: `frontend/src/AppRoutes.test.tsx`

- [ ] **Step 1: Add failing tests that prove the old styling residue is still present**

```tsx
it('does not rely on premium or glass utility naming in user-facing shared components', () => {
  render(<PlanCard {...planProps} />);
  expect(screen.getByTestId('plan-card').className).not.toMatch(/glass|premium/i);
});

it('keeps the language selector inside the same surface vocabulary as the rest of the shell', () => {
  render(<LanguageSelector />);
  expect(screen.getByRole('button')).toHaveClass('border-[color:var(--color-outline-variant)]');
});
```

- [ ] **Step 2: Run the cleanup-focused tests**

Run: `cd frontend && npm test -- src/shared/components/plans/PlanCard.test.tsx src/shared/components/ui/LanguageSelector.test.tsx src/AppRoutes.test.tsx`
Expected: FAIL because some old naming and styling assumptions still remain.

- [ ] **Step 3: Remove obsolete naming, align residual copy, and update all locales together**

```json
{
  "workouts": {
    "eyebrow": "Treinos",
    "subtitle": "Crie, organize e revise treinos com a mesma linguagem usada nas demais rotinas."
  },
  "nutrition": {
    "eyebrow": "Nutricao",
    "subtitle": "Registre refeicoes e acompanhe metas com o mesmo padrao estrutural do app."
  }
}
```

```tsx
export function LanguageSelector() {
  return (
    <Button
      type="button"
      variant="secondary"
      className="h-10 rounded-[var(--radius-md)] border-[color:var(--color-outline-variant)] px-3"
    >
      <Globe size={16} />
      {activeLabel}
    </Button>
  );
}
```

- [ ] **Step 4: Run the full frontend test suite for the redesign**

Run: `cd frontend && npm test`
Expected: PASS

- [ ] **Step 5: Run the final frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the cleanup, locale, and regression coverage pass**

```bash
git add frontend/src/shared/components/plans/PlanCard.tsx frontend/src/shared/components/plans/PlanCard.test.tsx frontend/src/shared/components/ui/LanguageSelector.tsx frontend/src/shared/components/ui/LanguageSelector.test.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json frontend/src/AppRoutes.test.tsx frontend/src/features frontend/src/shared/components
git commit -m "feat: complete unified redesign cleanup and locale alignment"
```

## Coverage Matrix

The migration is not complete until every main-app surface below has been refactored onto the unified system:

- Public entry: `/` via `frontend/src/features/landing/LandingPage.tsx`
- Authentication: `/login` and `/auth/action` via `frontend/src/features/auth/LoginPage.tsx` and `frontend/src/features/auth/ResetPasswordPage.tsx`
- Legal: `/termos-de-uso` and `/politica-de-privacidade` via `frontend/src/features/legal/TermsPage.tsx` and `frontend/src/features/legal/PrivacyPage.tsx`
- Onboarding: `/onboarding` via `frontend/src/features/onboarding/components/OnboardingPage.tsx`
- Dashboard: `/dashboard` via `frontend/src/features/dashboard/DashboardPage.tsx`
- Plan: `/dashboard/plan` via `frontend/src/features/plan/PlanPage.tsx`
- Workouts: `/dashboard/workouts` via `frontend/src/features/workouts/WorkoutsPage.tsx`
- Body: `/dashboard/body` via `frontend/src/features/body/BodyPage.tsx`
- Nutrition: `/dashboard/nutrition` via `frontend/src/features/nutrition/NutritionPage.tsx`
- Chat: `/dashboard/chat` via `frontend/src/features/chat/ChatPage.tsx`
- Settings shell: `/dashboard/settings` via `frontend/src/features/settings/SettingsPage.tsx`
- Profile: `/dashboard/settings/profile` via `frontend/src/features/settings/components/UserProfilePage.tsx`
- Subscription: `/dashboard/settings/subscription` via `frontend/src/features/settings/components/SubscriptionPage.tsx`
- Trainer settings: `/dashboard/settings/trainer` via `frontend/src/features/settings/components/TrainerSettingsPage.tsx`
- Integrations: `/dashboard/settings/integrations` via `frontend/src/features/settings/components/IntegrationsPage.tsx`
- Memories: `/dashboard/settings/memories` via `frontend/src/features/memories/MemoriesPage.tsx`

## Verification Checklist

- Run every focused suite listed in the tasks while migrating.
- Run `cd frontend && npm test` before closing the redesign.
- Run `cd frontend && npm run lint && npm run typecheck` after the final edit set.
- Ensure any new or changed user-facing text ships in `frontend/src/locales/pt-BR.json`, `frontend/src/locales/en-US.json`, and `frontend/src/locales/es-ES.json`.
- Confirm that add/edit workout, add/edit nutrition, and body-log entry all use the same form grammar.
- Confirm that workouts, nutrition records, and memories all use the same list grammar.
- Confirm that dashboard, plan, and progress views use the same insight-screen hierarchy.

## Spec Coverage Self-Review

- Global tokens, spacing, typography, shape, and dark-only surface rules are covered by Tasks 1 and 2.
- Shared styling contract, component defaults, and semantic states are covered by Tasks 1 through 3.
- New shared components and templates are covered by Task 3.
- Shell and navigation consistency are covered by Task 3.
- Public, onboarding, authenticated insight, list, form, conversation, and settings surfaces are covered by Tasks 4 through 7.
- Translation alignment and residual cleanup are covered by Task 8.
- The requirement to change all main-app screens is covered by the coverage matrix plus Tasks 4 through 7.
