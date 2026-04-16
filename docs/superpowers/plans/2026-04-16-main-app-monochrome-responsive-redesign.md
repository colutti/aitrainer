# Main App Monochrome Responsive Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the main app's glassy purple visual language with a monochrome dark system, then redesign the authenticated shell, dashboard, and chat to use desktop space intentionally across mobile, 1080p, 1440p, and 4K.

**Architecture:** Start from shared tokens and shell constraints so page changes inherit a stable visual system instead of layering one-off overrides. Implement route-aware width modes in the authenticated layout first, then redesign dashboard and chat on top of that foundation with TDD coverage for the new desktop structures.

**Tech Stack:** React 19, TypeScript, TailwindCSS v4, Vitest, Testing Library, Vite

---

### Task 1: Replace The Shared Visual Foundation

**Files:**
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/shared/styles/ui-variants.ts`
- Modify: `frontend/src/shared/components/ui/premium/PremiumCard.tsx`
- Modify: `frontend/src/shared/components/ui/premium/PremiumCard.test.tsx`
- Test: `frontend/src/shared/components/ui/premium/PremiumCard.test.tsx`

- [ ] **Step 1: Write the failing tests for the new solid-surface system**

```tsx
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { PremiumCard } from './PremiumCard';

describe('PremiumCard', () => {
  it('uses the solid workspace card classes instead of glassmorphism', () => {
    render(<PremiumCard data-testid="card">content</PremiumCard>);

    const card = screen.getByTestId('card');
    expect(card).toHaveClass('surface-card');
    expect(card).not.toHaveClass('glass-card');
    expect(card).not.toHaveClass('glass-card-hover');
  });

  it('applies the new hover treatment when enabled', () => {
    render(
      <PremiumCard data-testid="card" withHover>
        content
      </PremiumCard>
    );

    expect(screen.getByTestId('card')).toHaveClass('surface-card-hover');
  });
});
```

- [ ] **Step 2: Run the focused test to verify it fails for the right reason**

Run: `cd frontend && npm test -- src/shared/components/ui/premium/PremiumCard.test.tsx`
Expected: FAIL because `surface-card` and `surface-card-hover` do not exist in the current component output.

- [ ] **Step 3: Implement monochrome tokens and shared utilities**

```css
@theme {
  --font-display: 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --color-app-bg: #050505;
  --color-app-surface: #0d0d0d;
  --color-app-surface-raised: #141414;
  --color-app-border: #232323;
  --color-text-primary: #fafafa;
  --color-text-secondary: #b5b5b5;
  --color-text-muted: #7a7a7a;
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
}

@utility surface-card {
  @apply rounded-[24px] border border-[color:var(--color-app-border)] bg-[color:var(--color-app-surface)] text-[color:var(--color-text-primary)] transition-colors;
}

@utility surface-card-hover {
  @apply hover:bg-[color:var(--color-app-surface-raised)] hover:border-white/15;
}
```

```ts
export const PREMIUM_UI = {
  pageWrapper: 'min-h-screen bg-[color:var(--color-app-bg)] text-[color:var(--color-text-primary)] font-sans selection:bg-white/15 relative overflow-hidden',
  card: {
    base: 'surface-card',
    hover: 'surface-card-hover',
    padding: 'p-6 md:p-8',
  },
  button: {
    premium: 'btn-premium',
    glass: 'btn-glass',
    ghost: 'btn-ghost',
  },
};
```

- [ ] **Step 4: Run the focused test again**

Run: `cd frontend && npm test -- src/shared/components/ui/premium/PremiumCard.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the shared validation gate for the foundation changes**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the shared foundation**

```bash
git add frontend/src/index.css frontend/src/shared/styles/ui-variants.ts frontend/src/shared/components/ui/premium/PremiumCard.tsx frontend/src/shared/components/ui/premium/PremiumCard.test.tsx
git commit -m "feat: replace glass card foundation with monochrome surfaces"
```

### Task 2: Add Route-Aware Width Modes To The Authenticated Shell

**Files:**
- Modify: `frontend/src/shared/components/layout/PremiumLayout.tsx`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`
- Create: `frontend/src/shared/components/layout/layoutModes.ts`
- Test: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`

- [ ] **Step 1: Write the failing shell tests for width modes and cleaner desktop layout**

```tsx
it('applies the workspace width mode on dashboard routes', () => {
  (useAuthStore as any).mockReturnValue({
    userInfo: { name: 'Atlas User', email: 'atlas@fityq.it' },
    logout: vi.fn(),
  });

  render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <PremiumLayout />
    </MemoryRouter>
  );

  expect(screen.getByTestId('app-shell-main')).toHaveClass('max-w-[1920px]');
});

it('applies the conversation width mode on chat routes', () => {
  (useAuthStore as any).mockReturnValue({
    userInfo: { name: 'Atlas User', email: 'atlas@fityq.it' },
    logout: vi.fn(),
  });

  render(
    <MemoryRouter initialEntries={['/dashboard/chat']}>
      <PremiumLayout />
    </MemoryRouter>
  );

  expect(screen.getByTestId('app-shell-main')).toHaveClass('max-w-[2160px]');
  expect(screen.getByTestId('desktop-nav')).not.toHaveClass('backdrop-blur-xl');
});
```

- [ ] **Step 2: Run the shell tests to verify they fail**

Run: `cd frontend && npm test -- src/shared/components/layout/PremiumLayout.test.tsx`
Expected: FAIL because `app-shell-main` is missing, the width-mode classes do not exist, and the nav still uses blur-heavy classes.

- [ ] **Step 3: Implement route-aware layout modes**

```ts
export function getLayoutMode(pathname: string) {
  if (pathname.startsWith('/dashboard/chat')) {
    return {
      contentClassName: 'max-w-[2160px] px-4 md:px-8 xl:px-10 2xl:px-12',
      navClassName: 'px-4 md:px-8 xl:px-10 2xl:px-12',
    };
  }

  if (pathname === '/dashboard' || pathname.startsWith('/dashboard/body') || pathname.startsWith('/dashboard/workouts')) {
    return {
      contentClassName: 'max-w-[1920px] px-4 md:px-8 xl:px-10 2xl:px-12',
      navClassName: 'px-4 md:px-8 xl:px-10 2xl:px-12',
    };
  }

  return {
    contentClassName: 'max-w-[1600px] px-4 md:px-8 xl:px-10',
    navClassName: 'px-4 md:px-8 xl:px-10',
  };
}
```

```tsx
const layoutMode = getLayoutMode(location.pathname);

<nav
  data-testid="desktop-nav"
  className={cn(
    'hidden md:flex fixed top-0 left-0 right-0 h-18 items-center z-50 bg-[color:var(--color-app-bg)] border-b border-white/8',
    layoutMode.navClassName
  )}
>
```

```tsx
<div
  data-testid="app-shell-main"
  className={cn('mx-auto h-full min-h-0 w-full', layoutMode.contentClassName)}
>
  <Outlet />
</div>
```

- [ ] **Step 4: Re-run the shell tests**

Run: `cd frontend && npm test -- src/shared/components/layout/PremiumLayout.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the shell refactor**

```bash
git add frontend/src/shared/components/layout/PremiumLayout.tsx frontend/src/shared/components/layout/PremiumLayout.test.tsx frontend/src/shared/components/layout/layoutModes.ts
git commit -m "feat: add route-aware workspace widths to app shell"
```

### Task 3: Redesign The Dashboard Into A Desktop Workspace

**Files:**
- Modify: `frontend/src/features/dashboard/components/DashboardView.tsx`
- Modify: `frontend/src/features/dashboard/DashboardPage.test.tsx`
- Create: `frontend/src/features/dashboard/components/DashboardWorkspaceSection.tsx`
- Test: `frontend/src/features/dashboard/DashboardPage.test.tsx`

- [ ] **Step 1: Write the failing dashboard tests for the new desktop zones**

```tsx
it('renders the dashboard in primary, secondary, and tertiary zones', () => {
  vi.mocked(useDashboardStore).mockReturnValue({
    ...defaultHookValues,
    data: defaultData as any,
  });

  render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>
  );

  expect(screen.getByTestId('dashboard-workspace')).toBeInTheDocument();
  expect(screen.getByTestId('dashboard-primary-zone')).toBeInTheDocument();
  expect(screen.getByTestId('dashboard-secondary-zone')).toBeInTheDocument();
  expect(screen.getByTestId('dashboard-tertiary-zone')).toBeInTheDocument();
});

it('keeps the metabolism hero inside the primary zone', () => {
  vi.mocked(useDashboardStore).mockReturnValue({
    ...defaultHookValues,
    data: defaultData as any,
  });

  render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>
  );

  expect(screen.getByTestId('dashboard-primary-zone')).toContainElement(screen.getByTestId('widget-metabolism'));
});
```

- [ ] **Step 2: Run the dashboard tests to verify they fail**

Run: `cd frontend && npm test -- src/features/dashboard/DashboardPage.test.tsx`
Expected: FAIL because the workspace zones and test ids do not exist.

- [ ] **Step 3: Implement the dashboard workspace structure**

```tsx
<div data-testid="dashboard-workspace" className="space-y-6 pb-20">
  <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.75fr)] 2xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.75fr)] gap-6">
    <div data-testid="dashboard-primary-zone" className="space-y-6">
      <PremiumCard data-testid="widget-metabolism" className="p-6 xl:p-8 border-white/10 bg-[color:var(--color-app-surface-raised)]">
        {/* existing metabolism content, but without gradients and glows */}
      </PremiumCard>

      <div className="grid grid-cols-1 2xl:grid-cols-3 gap-6">
        {/* weight / fat / muscle cards */}
      </div>
    </div>

    <aside data-testid="dashboard-tertiary-zone" className="space-y-6">
      {/* streak, recent PRs, short status cards */}
    </aside>
  </section>

  <section data-testid="dashboard-secondary-zone" className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(320px,0.8fr)] gap-6">
    {/* radar, volume, weekly frequency, recent activity */}
  </section>
</div>
```

- [ ] **Step 4: Re-run the dashboard tests**

Run: `cd frontend && npm test -- src/features/dashboard/DashboardPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the dashboard validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the dashboard redesign**

```bash
git add frontend/src/features/dashboard/components/DashboardView.tsx frontend/src/features/dashboard/components/DashboardWorkspaceSection.tsx frontend/src/features/dashboard/DashboardPage.test.tsx
git commit -m "feat: redesign dashboard as responsive workspace"
```

### Task 4: Redesign Chat Into A Structured Conversation Workspace

**Files:**
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Modify: `frontend/src/features/chat/ChatPage.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.test.tsx`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Create: `frontend/src/features/chat/components/ChatContextPanel.tsx`
- Test: `frontend/src/features/chat/components/ChatView.test.tsx`
- Test: `frontend/src/features/chat/ChatPage.test.tsx`

- [ ] **Step 1: Write the failing chat tests for the new workspace structure**

```tsx
it('renders a chat workspace with conversation and context panel containers', () => {
  render(<ChatView {...mockProps} />);

  expect(screen.getByTestId('chat-workspace')).toBeInTheDocument();
  expect(screen.getByTestId('chat-conversation-column')).toBeInTheDocument();
  expect(screen.getByTestId('chat-context-panel')).toBeInTheDocument();
});

it('keeps the composer inside the conversation column', () => {
  render(<ChatView {...mockProps} />);

  expect(screen.getByTestId('chat-conversation-column')).toContainElement(screen.getByTestId('chat-form'));
});
```

```tsx
it('passes the resolved trainer into the context panel summary', () => {
  render(
    <MemoryRouter>
      <ChatPage />
    </MemoryRouter>
  );

  expect(screen.getByTestId('chat-context-trainer-name')).toHaveTextContent('Marcus');
});
```

- [ ] **Step 2: Run the chat tests to verify they fail**

Run: `cd frontend && npm test -- src/features/chat/components/ChatView.test.tsx src/features/chat/ChatPage.test.tsx`
Expected: FAIL because the new workspace containers and trainer context summary do not exist.

- [ ] **Step 3: Implement the chat workspace and context panel**

```tsx
<div data-testid="chat-workspace" className="grid h-full min-h-0 grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] 2xl:grid-cols-[minmax(240px,0.2fr)_minmax(0,0.9fr)_360px] gap-0">
  <section data-testid="chat-conversation-column" className="flex min-h-0 flex-col border-r border-white/8">
    {/* header, messages, composer */}
  </section>

  <aside data-testid="chat-context-panel" className="hidden xl:flex flex-col gap-4 bg-[color:var(--color-app-surface)] p-4 2xl:p-6">
    <ChatContextPanel
      trainerName={trainerName}
      trainerId={trainer?.trainer_id ?? null}
      isStreaming={isStreaming}
      messageCount={messages.length}
    />
  </aside>
</div>
```

```tsx
export function ChatContextPanel({ trainerName, trainerId, isStreaming, messageCount }: ChatContextPanelProps) {
  return (
    <div className="surface-card h-full p-4 md:p-5">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">Trainer</p>
      <h2 data-testid="chat-context-trainer-name" className="mt-2 text-lg font-black text-[color:var(--color-text-primary)]">
        {trainerName}
      </h2>
      <p className="mt-4 text-sm text-[color:var(--color-text-secondary)]">
        {isStreaming ? 'Responding now' : `${messageCount.toString()} messages in this conversation`}
      </p>
      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
        {trainerId ?? 'default-trainer'}
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Re-run the chat tests**

Run: `cd frontend && npm test -- src/features/chat/components/ChatView.test.tsx src/features/chat/ChatPage.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the chat redesign**

```bash
git add frontend/src/features/chat/components/ChatView.tsx frontend/src/features/chat/ChatPage.tsx frontend/src/features/chat/components/ChatView.test.tsx frontend/src/features/chat/ChatPage.test.tsx frontend/src/features/chat/components/ChatContextPanel.tsx
git commit -m "feat: redesign chat as desktop conversation workspace"
```

### Task 5: Align Secondary In-App Surfaces To The New System

**Files:**
- Modify: `frontend/src/features/settings/SettingsPage.tsx`
- Modify: `frontend/src/features/body/BodyPage.tsx`
- Modify: `frontend/src/features/workouts/WorkoutsPage.tsx`
- Modify: `frontend/src/shared/components/ui/Button.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write a failing regression test that asserts the app shell still renders route content after the shared style migration**

```tsx
it('renders authenticated route content inside the monochrome shell', async () => {
  render(<App />);

  expect(await screen.findByTestId('desktop-nav')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the regression test to verify it fails for the right reason**

Run: `cd frontend && npm test -- src/App.test.tsx`
Expected: FAIL if the current test file does not cover the new shell contract or lacks the updated route assumptions.

- [ ] **Step 3: Apply targeted alignment to secondary app pages**

```tsx
<section className="mx-auto w-full max-w-[1600px] space-y-6">
  {/* existing page content, but using surface-card, stronger borders, and the new spacing bands */}
</section>
```

```tsx
secondary: 'bg-[color:var(--color-app-surface-raised)] border border-white/10 text-[color:var(--color-text-primary)] hover:bg-[#1a1a1a]',
```

- [ ] **Step 4: Re-run the regression test**

Run: `cd frontend && npm test -- src/App.test.tsx`
Expected: PASS

- [ ] **Step 5: Run the full frontend validation gate**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 6: Commit the alignment pass**

```bash
git add frontend/src/features/settings/SettingsPage.tsx frontend/src/features/body/BodyPage.tsx frontend/src/features/workouts/WorkoutsPage.tsx frontend/src/shared/components/ui/Button.tsx frontend/src/App.test.tsx
git commit -m "refactor: align secondary app pages with monochrome shell"
```

### Task 6: Final Verification And Residual Test Coverage

**Files:**
- Modify: `frontend/src/features/dashboard/DashboardPage.test.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.test.tsx`
- Modify: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/src/shared/components/layout/PremiumLayout.test.tsx`

- [ ] **Step 1: Add residual regression cases for desktop structure and mobile safety**

```tsx
it('keeps mobile navigation rendered after the shell redesign', () => {
  render(
    <MemoryRouter initialEntries={['/dashboard/chat']}>
      <PremiumLayout />
    </MemoryRouter>
  );

  expect(screen.getByTestId('mobile-nav')).toBeInTheDocument();
});

it('renders the chat context panel container without breaking the empty state', () => {
  render(<ChatView {...mockProps} messages={[]} />);

  expect(screen.getByTestId('chat-context-panel')).toBeInTheDocument();
  expect(screen.getByText('chat.start_conversation')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted regression suite**

Run: `cd frontend && npm test -- src/shared/components/layout/PremiumLayout.test.tsx src/features/dashboard/DashboardPage.test.tsx src/features/chat/components/ChatView.test.tsx src/features/chat/ChatPage.test.tsx`
Expected: PASS

- [ ] **Step 3: Run the required frontend gate one final time**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Run the broader frontend test suite**

Run: `cd frontend && npm test`
Expected: PASS

- [ ] **Step 5: Commit the verification sweep**

```bash
git add frontend/src/shared/components/layout/PremiumLayout.test.tsx frontend/src/features/dashboard/DashboardPage.test.tsx frontend/src/features/chat/components/ChatView.test.tsx frontend/src/features/chat/ChatPage.test.tsx
git commit -m "test: cover monochrome shell and workspace layouts"
```
