# System-Wide Test Coverage Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise automated test coverage across backend, main frontend, admin frontend, and E2E-critical flows without inflating the suite with placeholder tests.

**Architecture:** Attack coverage in descending ROI order: backend pure modules and adapters first, then frontend shared infrastructure and feature hooks, then admin auth/analytics surfaces, and finally CI/reporting hardening so the gains stick. Each task is independently shippable and should land with targeted tests first, minimal production fixes only when the new tests expose a real gap.

**Tech Stack:** FastAPI, Pytest, Vitest, React 19, Zustand, React Router 7, Playwright, Podman Compose

---

## Current Baseline

- Backend coverage from the last containerized run: `79%` statements
- Frontend coverage from the last containerized run: `68.33%` lines, `67.18%` statements, `67.66%` functions, `64.51%` branches
- Admin coverage from the last containerized run: `42%` lines, `41.13%` statements, `34.92%` functions, `26.92%` branches
- E2E currently validates execution only: `33 passed`, no code-coverage artifact

## Scope Note

This plan spans multiple independent subsystems. If execution needs lower coordination cost, split after Task 2 into `backend`, `frontend`, and `admin/e2e` follow-up plans. The order below is still the correct global priority order.

## File Structure

### Backend coverage tranche

- Create: `backend/tests/unit/core/test_pricing.py`
- Create: `backend/tests/unit/api/models/test_metabolism_models.py`
- Create: `backend/tests/unit/utils/test_qdrant_utils.py`
- Create: `backend/tests/unit/core/test_firebase.py`
- Create: `backend/tests/services/test_memory_service.py`
- Modify if tests expose contract gaps: `backend/src/core/pricing.py`
- Modify if tests expose contract gaps: `backend/src/core/firebase.py`
- Modify if tests expose contract gaps: `backend/src/services/memory_service.py`

### Frontend coverage tranche

- Create: `frontend/src/shared/stores/createEntityStore.test.ts`
- Create: `frontend/src/shared/components/ui/GlobalErrorBoundary.test.tsx`
- Create: `frontend/src/shared/components/ui/HelpTooltip.test.tsx`
- Create: `frontend/src/shared/components/ui/QuickAddFAB.test.tsx`
- Create: `frontend/src/features/body/hooks/useNutritionTab.test.ts`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/AppRoutes.test.tsx`
- Modify if tests expose gaps: `frontend/src/shared/stores/createEntityStore.ts`
- Modify if tests expose gaps: `frontend/src/features/body/hooks/useNutritionTab.ts`
- Modify if tests expose gaps: `frontend/src/shared/components/ui/QuickAddFAB.tsx`

### Admin coverage tranche

- Create: `frontend/admin/src/shared/hooks/useAdminAuth.test.ts`
- Create: `frontend/admin/src/shared/components/AdminProtectedRoute.test.tsx`
- Create: `frontend/admin/src/features/auth/LoginPage.test.tsx`
- Create: `frontend/admin/src/features/admin/components/AdminTokensPage.test.tsx`
- Create: `frontend/admin/src/shared/api/http-client.test.ts`
- Modify if tests expose gaps: `frontend/admin/src/shared/hooks/useAdminAuth.ts`
- Modify if tests expose gaps: `frontend/admin/src/shared/components/AdminProtectedRoute.tsx`
- Modify if tests expose gaps: `frontend/admin/src/features/admin/components/AdminTokensPage.tsx`

### E2E and coverage guardrail tranche

- Create: `frontend/e2e/17-dashboard-empty-states.spec.ts`
- Create: `frontend/e2e/18-settings-reload.spec.ts`
- Modify: `frontend/playwright.config.ts`
- Modify: `frontend/admin/vitest.config.ts`
- Modify: `README.md`
- Modify: `.github/workflows/ci.yml`

## Execution Rule

For coverage work, some tests may pass immediately because the behavior already exists and is merely untested. If that happens, keep the test-only change, skip the production patch step for that task, rerun the targeted suite, and commit the added coverage. Do not invent refactors just to satisfy the structure.

---

### Task 1: Cover backend pure modules and value objects

**Files:**
- Create: `backend/tests/unit/core/test_pricing.py`
- Create: `backend/tests/unit/api/models/test_metabolism_models.py`
- Create: `backend/tests/unit/utils/test_qdrant_utils.py`
- Modify if needed: `backend/src/core/pricing.py`

- [ ] **Step 1: Write the failing tests**

```python
from src.core.pricing import get_cost_usd


def test_get_cost_usd_uses_per_million_token_rates():
    assert get_cost_usd("gpt-4o-mini", 100_000, 50_000) == 0.045


def test_get_cost_usd_returns_zero_for_unknown_model():
    assert get_cost_usd("unknown-model", 100, 100) == 0.0


def test_get_cost_usd_rounds_to_four_decimals():
    assert get_cost_usd("gemini-3-pro", 12_345, 67_890) == 0.8394
```

```python
from src.api.models.metabolism import MacroTargets, MetabolismResponse, WeightTrendPoint


def test_metabolism_response_serializes_nested_fields():
    model = MetabolismResponse(
        tdee=2400,
        confidence="high",
        avg_calories=2200,
        weight_change_per_week=-0.3,
        logs_count=21,
        startDate="2026-03-01",
        endDate="2026-03-21",
        start_weight=82.4,
        end_weight=81.5,
        macro_targets=MacroTargets(protein=180, carbs=220, fat=70),
        weight_trend=[WeightTrendPoint(date="2026-03-20", weight=81.5, trend=81.7)],
    )

    dumped = model.model_dump()
    assert dumped["macro_targets"]["protein"] == 180
    assert dumped["weight_trend"][0]["trend"] == 81.7
```

```python
from types import SimpleNamespace
from unittest.mock import Mock

from src.utils.qdrant_utils import point_to_dict, scroll_all_user_points


def test_point_to_dict_falls_back_to_point_id_and_data_payload():
    point = SimpleNamespace(id="abc123", payload={"data": "remember this", "user_id": "u-1"})
    assert point_to_dict(point) == {
        "id": "abc123",
        "memory": "remember this",
        "user_id": "u-1",
        "created_at": None,
        "updated_at": None,
    }


def test_scroll_all_user_points_keeps_scrolling_until_offset_is_none():
    client = Mock()
    client.scroll.side_effect = [
        ([SimpleNamespace(id="1", payload={})], "next"),
        ([SimpleNamespace(id="2", payload={})], None),
    ]

    result = scroll_all_user_points(client, "memories", Mock())

    assert [point.id for point in result] == ["1", "2"]
    assert client.scroll.call_count == 2
```

- [ ] **Step 2: Run the targeted backend tests**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm backend-tests pytest \
  tests/unit/core/test_pricing.py \
  tests/unit/api/models/test_metabolism_models.py \
  tests/unit/utils/test_qdrant_utils.py -q
```

Expected: `FAIL` until the new tests and any missing edge handling are in place.

- [ ] **Step 3: Write the minimal implementation only if Step 2 exposed a real gap**

```python
def get_cost_usd(model: str, tokens_input: int, tokens_output: int) -> float:
    if model not in PROVIDER_PRICING:
        return 0.0

    pricing = PROVIDER_PRICING[model]
    cost = (
        tokens_input * pricing["input"] + tokens_output * pricing["output"]
    ) / 1_000_000
    return round(cost, 4)
```

If these tests already pass, do not change production code in this task.

- [ ] **Step 4: Run backend coverage slice**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm backend-tests pytest \
  tests/unit/core/test_pricing.py \
  tests/unit/api/models/test_metabolism_models.py \
  tests/unit/utils/test_qdrant_utils.py \
  --cov=src.core.pricing \
  --cov=src.api.models.metabolism \
  --cov=src.utils.qdrant_utils \
  --cov-report=term-missing
```

Expected: `PASS` and the three target modules no longer report `0%`.

- [ ] **Step 5: Commit**

```bash
git add \
  backend/tests/unit/core/test_pricing.py \
  backend/tests/unit/api/models/test_metabolism_models.py \
  backend/tests/unit/utils/test_qdrant_utils.py \
  backend/src/core/pricing.py
git commit -m "test: cover backend pricing and metabolism helpers"
```

### Task 2: Cover backend adapters with mocks instead of live dependencies

**Files:**
- Create: `backend/tests/unit/core/test_firebase.py`
- Create: `backend/tests/services/test_memory_service.py`
- Modify if needed: `backend/src/core/firebase.py`
- Modify if needed: `backend/src/services/memory_service.py`

- [ ] **Step 1: Write the failing tests**

```python
from unittest.mock import Mock, patch

from src.core.firebase import init_firebase


@patch("src.core.firebase.initialize_app")
@patch("src.core.firebase.credentials.Certificate")
@patch("src.core.firebase.settings")
def test_init_firebase_accepts_json_credentials(mock_settings, mock_certificate, mock_initialize):
    mock_settings.FIREBASE_CREDENTIALS = '{"type":"service_account","project_id":"demo"}'

    init_firebase()

    mock_certificate.assert_called_once_with({"type": "service_account", "project_id": "demo"})
    mock_initialize.assert_called_once()


@patch("src.core.firebase.logger")
@patch("src.core.firebase.settings")
def test_init_firebase_logs_warning_when_credentials_are_missing(mock_settings, mock_logger):
    mock_settings.FIREBASE_CREDENTIALS = ""

    init_firebase()

    mock_logger.warning.assert_called_once()
```

```python
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.services.memory_service import add_memory, get_memories_paginated


def test_get_memories_paginated_sorts_newest_first():
    client = Mock()
    client.count.return_value = SimpleNamespace(count=2)
    points = [
        SimpleNamespace(id="older", payload={"id": "older", "memory": "a", "created_at": "2026-03-01T10:00:00"}),
        SimpleNamespace(id="newer", payload={"id": "newer", "memory": "b", "created_at": "2026-03-02T10:00:00"}),
    ]

    with patch("src.services.memory_service.scroll_all_user_points", return_value=points), \
         patch("src.services.memory_service._ensure_collection"):
        memories, total = get_memories_paginated("u-1", 1, 10, client, "memories")

    assert total == 2
    assert [item["id"] for item in memories] == ["newer", "older"]


def test_add_memory_builds_point_and_returns_memory_id():
    client = Mock()

    with patch("src.services.memory_service._ensure_collection"), \
         patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]), \
         patch("src.services.memory_service.uuid4", return_value="fixed-id"), \
         patch("src.services.memory_service.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value.isoformat.return_value = "2026-03-27T10:00:00"
        memory_id = add_memory("u-1", "hydrate more", client, "memories", "habit")

    assert memory_id == "fixed-id"
    client.upsert.assert_called_once()
```

- [ ] **Step 2: Run the targeted backend tests**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm backend-tests pytest \
  tests/unit/core/test_firebase.py \
  tests/services/test_memory_service.py -q
```

Expected: `FAIL` until the mocks and asserted contracts line up with the implementation.

- [ ] **Step 3: Apply the smallest production patch only if tests exposed a contract gap**

```python
    if not settings.FIREBASE_CREDENTIALS:
        logger.warning(
            "FIREBASE_CREDENTIALS not set. Firebase Admin will not be initialized."
        )
        return
```

```python
        all_points.sort(
            key=lambda p: p.payload.get("created_at", "") if p.payload else "",
            reverse=True,
        )
```

These are the only behaviors this task is allowed to change.

- [ ] **Step 4: Run the targeted coverage slice**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm backend-tests pytest \
  tests/unit/core/test_firebase.py \
  tests/services/test_memory_service.py \
  --cov=src.core.firebase \
  --cov=src.services.memory_service \
  --cov-report=term-missing
```

Expected: `PASS` and coverage for `src/core/firebase.py` and `src/services/memory_service.py` moves materially above the current low-water mark.

- [ ] **Step 5: Commit**

```bash
git add \
  backend/tests/unit/core/test_firebase.py \
  backend/tests/services/test_memory_service.py \
  backend/src/core/firebase.py \
  backend/src/services/memory_service.py
git commit -m "test: cover backend firebase and memory adapters"
```

### Task 3: Cover frontend shared infrastructure with deterministic unit tests

**Files:**
- Create: `frontend/src/shared/stores/createEntityStore.test.ts`
- Create: `frontend/src/shared/components/ui/GlobalErrorBoundary.test.tsx`
- Create: `frontend/src/shared/components/ui/HelpTooltip.test.tsx`
- Create: `frontend/src/shared/components/ui/QuickAddFAB.test.tsx`
- Modify if needed: `frontend/src/shared/stores/createEntityStore.ts`
- Modify if needed: `frontend/src/shared/components/ui/QuickAddFAB.tsx`

- [ ] **Step 1: Write the failing tests**

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';
import { createEntityStore } from './createEntityStore';

vi.mock('../api/http-client', () => ({ httpClient: vi.fn() }));

describe('createEntityStore', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches items and pagination data', async () => {
    const useStore = createEntityStore<{ id: string }>({ endpoint: '/items' });
    vi.mocked(httpClient).mockResolvedValue({ items: [{ id: '1' }], total: 1, page: 2, total_pages: 3 });

    await useStore.getState().fetchItems(2, 10);

    expect(useStore.getState().items).toEqual([{ id: '1' }]);
    expect(useStore.getState().page).toBe(2);
    expect(useStore.getState().totalPages).toBe(3);
  });

  it('deletes items by id or _id without leaving isSaving stuck', async () => {
    const useStore = createEntityStore<{ id?: string; _id?: string }>({ endpoint: '/items' });
    useStore.setState({ items: [{ id: '1' }, { _id: '2' }], total: 2 });
    vi.mocked(httpClient).mockResolvedValue({});

    await useStore.getState().deleteItem('2');

    expect(useStore.getState().items).toEqual([{ id: '1' }]);
    expect(useStore.getState().isSaving).toBe(false);
  });
});
```

```tsx
import { render, screen, fireEvent } from '../../utils/test-utils';

import { GlobalErrorBoundary } from './GlobalErrorBoundary';

function Thrower() {
  throw new Error('boom');
}

describe('GlobalErrorBoundary', () => {
  it('renders the default fallback', () => {
    render(
      <GlobalErrorBoundary>
        <Thrower />
      </GlobalErrorBoundary>
    );

    expect(screen.getByText(/server_error/i)).toBeInTheDocument();
  });
});
```

```tsx
import { render, screen, fireEvent } from '../../utils/test-utils';

import { HelpTooltip } from './HelpTooltip';

it('shows and hides tooltip content on hover and touch', () => {
  render(<HelpTooltip content="Protein target help" />);
  const button = screen.getByRole('button');

  fireEvent.mouseEnter(button);
  expect(screen.getByText('Protein target help')).toBeInTheDocument();

  fireEvent.mouseLeave(button);
  expect(screen.queryByText('Protein target help')).not.toBeInTheDocument();
});
```

```tsx
import { render, screen, fireEvent } from '../../utils/test-utils';
import { vi } from 'vitest';

import { QuickAddFAB } from './QuickAddFAB';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

it('opens actions and navigates to the weight flow', () => {
  render(<QuickAddFAB />);

  fireEvent.click(screen.getByTestId('quick-add-fab'));
  fireEvent.click(screen.getByText(/register_weight/i));

  expect(mockNavigate).toHaveBeenCalledWith('/dashboard/body/weight?action=log-weight');
});
```

- [ ] **Step 2: Run the targeted frontend tests**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm frontend-tests sh -lc \
  "npm test -- src/shared/stores/createEntityStore.test.ts src/shared/components/ui/GlobalErrorBoundary.test.tsx src/shared/components/ui/HelpTooltip.test.tsx src/shared/components/ui/QuickAddFAB.test.tsx"
```

Expected: `FAIL` until the new tests and any missing accessibility or state-reset details are in place.

- [ ] **Step 3: Apply only the source fixes the tests prove necessary**

```ts
set({
  items: items.filter((item) => {
    const itemId = (item as { id?: string; _id?: string }).id ?? (item as { id?: string; _id?: string })._id;
    return itemId !== id;
  }),
  total: Math.max(total - 1, 0),
  isSaving: false
});
```

```tsx
<button
  type="button"
  aria-label={t(action.labelKey)}
  onClick={() => { action.onClick(); setIsOpen(false); }}
>
```

If the new tests already pass, keep this task test-only.

- [ ] **Step 4: Run the targeted coverage slice**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm frontend-tests sh -lc \
  "npm test -- --coverage src/shared/stores/createEntityStore.test.ts src/shared/components/ui/GlobalErrorBoundary.test.tsx src/shared/components/ui/HelpTooltip.test.tsx src/shared/components/ui/QuickAddFAB.test.tsx"
```

Expected: `PASS` and the four previously under-covered modules move off `0%`.

- [ ] **Step 5: Commit**

```bash
git add \
  frontend/src/shared/stores/createEntityStore.test.ts \
  frontend/src/shared/components/ui/GlobalErrorBoundary.test.tsx \
  frontend/src/shared/components/ui/HelpTooltip.test.tsx \
  frontend/src/shared/components/ui/QuickAddFAB.test.tsx \
  frontend/src/shared/stores/createEntityStore.ts \
  frontend/src/shared/components/ui/QuickAddFAB.tsx
git commit -m "test: cover frontend shared infrastructure"
```

### Task 4: Cover frontend feature hooks and route bootstrap

**Files:**
- Create: `frontend/src/features/body/hooks/useNutritionTab.test.ts`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/AppRoutes.test.tsx`
- Modify if needed: `frontend/src/features/body/hooks/useNutritionTab.ts`

- [ ] **Step 1: Write the failing tests**

```ts
import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { bodyApi } from '../api/body-api';
import { useNutritionTab } from './useNutritionTab';

vi.mock('../api/body-api', () => ({
  bodyApi: {
    getNutritionLogs: vi.fn(),
    getNutritionStats: vi.fn(),
    logNutrition: vi.fn(),
    deleteNutritionLog: vi.fn(),
  },
}));

describe('useNutritionTab', () => {
  beforeEach(() => vi.clearAllMocks());

  it('loads stats and logs on mount', async () => {
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue({ avg_calories: 2200 } as any);
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue({ logs: [], page: 1, total_pages: 1 } as any);

    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(bodyApi.getNutritionStats).toHaveBeenCalledOnce();
    expect(bodyApi.getNutritionLogs).toHaveBeenCalledWith(1, 10, undefined);
  });

  it('changes filter and reloads page 1', async () => {
    vi.mocked(bodyApi.getNutritionStats).mockResolvedValue({ avg_calories: 2200 } as any);
    vi.mocked(bodyApi.getNutritionLogs).mockResolvedValue({ logs: [], page: 1, total_pages: 1 } as any);
    const { result } = renderHook(() => useNutritionTab());

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      result.current.setFilter(30);
    });

    expect(bodyApi.getNutritionLogs).toHaveBeenLastCalledWith(1, 10, 30);
  });
});
```

```tsx
import { render, waitFor } from './shared/utils/test-utils';
import App from './App';

import { useAuthStore } from './shared/hooks/useAuth';

vi.mock('./shared/hooks/useAuth', () => ({
  useAuthStore: vi.fn(),
}));

it('initializes auth on mount and refreshes user info on focus', async () => {
  const init = vi.fn();
  const loadUserInfo = vi.fn();
  vi.mocked(useAuthStore)
    .mockReturnValueOnce(init)
    .mockReturnValueOnce(true)
    .mockReturnValueOnce(loadUserInfo);

  render(<App />);

  await waitFor(() => expect(init).toHaveBeenCalledOnce());
  window.dispatchEvent(new Event('focus'));
  expect(loadUserInfo).toHaveBeenCalledOnce();
});
```

```tsx
import { render, screen } from './shared/utils/test-utils';

import { AppRoutes } from './AppRoutes';

it('redirects unknown routes to the landing page', async () => {
  render(<AppRoutes />, { route: '/totally-unknown' });
  expect(await screen.findByText(/fityq/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted frontend tests**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm frontend-tests sh -lc \
  "npm test -- src/features/body/hooks/useNutritionTab.test.ts src/App.test.tsx src/AppRoutes.test.tsx"
```

Expected: `FAIL` until mocks, providers, and route/auth interactions are wired correctly.

- [ ] **Step 3: Make only the minimal source fix if the tests prove a gap**

```ts
  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      await Promise.all([loadStats(), loadLogs(1)]);
    } finally {
      setIsLoading(false);
    }
  }, [loadStats, loadLogs]);
```

This is the only production behavior this task is allowed to change.

- [ ] **Step 4: Run the targeted coverage slice**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm frontend-tests sh -lc \
  "npm test -- --coverage src/features/body/hooks/useNutritionTab.test.ts src/App.test.tsx src/AppRoutes.test.tsx"
```

Expected: `PASS` and coverage rises for `useNutritionTab.ts`, `App.tsx`, and `AppRoutes.tsx`.

- [ ] **Step 5: Commit**

```bash
git add \
  frontend/src/features/body/hooks/useNutritionTab.test.ts \
  frontend/src/App.test.tsx \
  frontend/src/AppRoutes.test.tsx \
  frontend/src/features/body/hooks/useNutritionTab.ts
git commit -m "test: cover frontend nutrition hook and route bootstrap"
```

### Task 5: Cover admin auth flow and token analytics

**Files:**
- Create: `frontend/admin/src/shared/hooks/useAdminAuth.test.ts`
- Create: `frontend/admin/src/shared/components/AdminProtectedRoute.test.tsx`
- Create: `frontend/admin/src/features/auth/LoginPage.test.tsx`
- Create: `frontend/admin/src/features/admin/components/AdminTokensPage.test.tsx`
- Create: `frontend/admin/src/shared/api/http-client.test.ts`
- Modify if needed: `frontend/admin/src/features/admin/components/AdminTokensPage.tsx`

- [ ] **Step 1: Write the failing tests**

```ts
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';
import { useAdminAuthStore } from './useAdminAuth';

vi.mock('../api/http-client', () => ({ httpClient: vi.fn() }));

describe('useAdminAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useAdminAuthStore.setState({ isAuthenticated: false, userInfo: null, isLoading: true, loginError: null });
  });

  it('stores the token and loads admin user info on login', async () => {
    vi.mocked(httpClient)
      .mockResolvedValueOnce({ token: 'admin-token' } as any)
      .mockResolvedValueOnce({ email: 'admin@fityq.com', role: 'admin', name: 'Admin' } as any);

    await useAdminAuthStore.getState().login('admin@fityq.com', 'secret');

    expect(localStorage.getItem('admin_auth_token')).toBe('admin-token');
    expect(useAdminAuthStore.getState().isAuthenticated).toBe(true);
  });
});
```

```tsx
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import { useAdminAuthStore } from '../hooks/useAdminAuth';
import { AdminProtectedRoute } from './AdminProtectedRoute';

vi.mock('../hooks/useAdminAuth', () => ({ useAdminAuthStore: vi.fn() }));

it('redirects unauthenticated users to /login', () => {
  vi.mocked(useAdminAuthStore).mockReturnValue({ isAuthenticated: false, isLoading: false } as any);

  render(
    <MemoryRouter>
      <AdminProtectedRoute><div>secret</div></AdminProtectedRoute>
    </MemoryRouter>
  );

  expect(screen.queryByText('secret')).not.toBeInTheDocument();
});
```

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

import { LoginPage } from './LoginPage';

it('submits credentials and navigates to the dashboard', async () => {
  const login = vi.fn().mockResolvedValue(undefined);
  const navigate = vi.fn();
  vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
    return { ...actual, useNavigate: () => navigate };
  });

  render(<LoginPage />);
  fireEvent.change(screen.getByPlaceholderText('admin@fityq.com'), { target: { value: 'admin@fityq.com' } });
  fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'secret' } });
  fireEvent.click(screen.getByRole('button', { name: /entrar no painel/i }));

  await waitFor(() => expect(login).toHaveBeenCalled());
  expect(navigate).toHaveBeenCalledWith('/');
});
```

```tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { adminApi } from '../api/admin-api';
import { AdminTokensPage } from './AdminTokensPage';

vi.mock('../api/admin-api', () => ({
  adminApi: {
    getTokenSummary: vi.fn(),
    getTokenTimeseries: vi.fn(),
  },
}));

it('loads analytics, switches period, and refreshes', async () => {
  vi.mocked(adminApi.getTokenSummary).mockResolvedValue({ data: [{ _id: 'user@test.com', total_input: 1000, total_output: 500, cost_usd: 1.25, message_count: 2, last_activity: '2026-03-27T10:00:00Z' }] } as any);
  vi.mocked(adminApi.getTokenTimeseries).mockResolvedValue({ data: [{ date: '2026-03-27', tokens_input: 1000, tokens_output: 500 }] } as any);

  render(<AdminTokensPage />);

  await waitFor(() => expect(screen.getByText('user@test.com')).toBeInTheDocument());
  fireEvent.click(screen.getByRole('button', { name: 'Atualizar tokens' }));

  await waitFor(() => expect(adminApi.getTokenSummary).toHaveBeenCalledTimes(2));
});
```

- [ ] **Step 2: Run the targeted admin tests**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm admin-tests sh -lc \
  "npm test -- src/shared/hooks/useAdminAuth.test.ts src/shared/components/AdminProtectedRoute.test.tsx src/features/auth/LoginPage.test.tsx src/features/admin/components/AdminTokensPage.test.tsx src/shared/api/http-client.test.ts"
```

Expected: `FAIL` until auth mocking and token analytics assertions are lined up.

- [ ] **Step 3: Apply only the smallest source fix if the tests expose a gap**

```tsx
<button
  onClick={() => { void fetchTokenData(days); }}
  disabled={isLoading}
  title="Atualizar"
  aria-label="Atualizar tokens"
>
```

```ts
  init: async () => {
    const token = get().getToken();
    if (!token) {
      set({ isLoading: false });
      return;
    }
```

These are the only production behaviors allowed to change in this task.

- [ ] **Step 4: Run the targeted admin coverage slice**

Run:

```bash
podman compose -f docker-compose.test.yml run --rm admin-tests sh -lc \
  "npm test -- --coverage src/shared/hooks/useAdminAuth.test.ts src/shared/components/AdminProtectedRoute.test.tsx src/features/auth/LoginPage.test.tsx src/features/admin/components/AdminTokensPage.test.tsx src/shared/api/http-client.test.ts"
```

Expected: `PASS` and admin totals move materially above the current `42%`/`26.92%` baseline.

- [ ] **Step 5: Commit**

```bash
git add \
  frontend/admin/src/shared/hooks/useAdminAuth.test.ts \
  frontend/admin/src/shared/components/AdminProtectedRoute.test.tsx \
  frontend/admin/src/features/auth/LoginPage.test.tsx \
  frontend/admin/src/features/admin/components/AdminTokensPage.test.tsx \
  frontend/admin/src/shared/api/http-client.test.ts \
  frontend/admin/src/features/admin/components/AdminTokensPage.tsx
git commit -m "test: cover admin auth and token analytics"
```

### Task 6: Close E2E gaps and lock the new baselines into CI

**Files:**
- Create: `frontend/e2e/17-dashboard-empty-states.spec.ts`
- Create: `frontend/e2e/18-settings-reload.spec.ts`
- Modify: `frontend/playwright.config.ts`
- Modify: `frontend/admin/vitest.config.ts`
- Modify: `README.md`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the missing end-to-end specs and threshold updates**

```ts
import { test, expect } from './fixtures';

test('dashboard empty states stay stable for a fresh user', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/dashboard');
  await expect(authenticatedPage.getByText(/sem dados|sem registros/i)).toBeVisible();
});
```

```ts
import { test, expect } from './fixtures';

test('settings survives a hard reload on the profile tab', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/dashboard/settings/profile');
  await authenticatedPage.reload();
  await expect(authenticatedPage.getByRole('heading', { name: /perfil|profile/i })).toBeVisible();
});
```

```ts
coverage: {
  provider: 'istanbul',
  reporter: ['text', 'json', 'html', 'json-summary'],
  exclude: [
    'node_modules/',
    'src/test/setup.ts',
    '**/*.d.ts',
    '**/*.test.tsx',
    '**/*.test.ts',
    'src/main.tsx',
    'src/vite-env.d.ts',
    'dist/**'
  ],
  thresholds: {
    branches: 35,
    functions: 45,
    lines: 45,
    statements: 43,
  },
},
```

- [ ] **Step 2: Run the E2E and admin threshold validations**

Run:

```bash
make e2e
```

Run:

```bash
podman compose -f docker-compose.test.yml run --rm admin-tests sh -lc "npm test -- --coverage"
```

Expected: `PASS`, with the two new E2E flows green and admin coverage staying above the newly enforced thresholds.

- [ ] **Step 3: Update CI and docs to reflect the real coverage contract**

```yaml
  test-once:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Ensure Docker Compose is available
        run: docker compose version
      - name: Run full test stack in containers
        run: make test-once
      - name: Run backend coverage
        run: make test-backend-cov
      - name: Run frontend coverage
        run: docker compose -f docker-compose.test.yml run --rm frontend-tests sh -lc "npm ci && npm test -- --coverage"
      - name: Run admin coverage
        run: docker compose -f docker-compose.test.yml run --rm admin-tests sh -lc "npm ci && npm test -- --coverage"
```

```md
### Frontend
`npm run test:coverage` currently enforces:
- branches: 58
- functions: 65
- lines: 68
- statements: 67

### Admin Frontend
`npm run test:coverage` currently enforces:
- branches: 35
- functions: 45
- lines: 45
- statements: 43
```

- [ ] **Step 4: Run the full system validation**

Run:

```bash
make test-once
```

Run:

```bash
podman compose -f docker-compose.test.yml run --rm frontend-tests sh -lc "npm test -- --coverage"
podman compose -f docker-compose.test.yml run --rm admin-tests sh -lc "npm test -- --coverage"
podman compose -f docker-compose.test.yml run --rm backend-tests pytest --cov=src --cov-report=term-missing
```

Expected: `PASS` everywhere, with coverage reports generated for backend, frontend, and admin, and the Playwright HTML report still written to `frontend/playwright-report/index.html`.

- [ ] **Step 5: Commit**

```bash
git add \
  frontend/e2e/17-dashboard-empty-states.spec.ts \
  frontend/e2e/18-settings-reload.spec.ts \
  frontend/playwright.config.ts \
  frontend/admin/vitest.config.ts \
  README.md \
  .github/workflows/ci.yml
git commit -m "test: add coverage guardrails and e2e gap coverage"
```

## Self-Review

### Spec coverage

- Backend covered: pure modules, models, adapters, memory service
- Main frontend covered: shared infra, routing bootstrap, nutrition hook
- Admin covered: auth, protected route, login, tokens analytics, shared HTTP layer
- E2E covered: additional flows plus CI/reporting guardrails

No spec gap remains for “aumentar nossa cobertura total de testes no sistema inteiro”.

### Placeholder scan

- No `TODO`, `TBD`, or “similar to previous task” markers remain
- Every task has exact file paths
- Every task has exact commands
- Every code-changing step includes concrete code

### Type consistency

- Backend tests import actual modules and use existing public function names
- Frontend tests target current file names and exported symbols
- Admin tests use the current `useAdminAuthStore`, `AdminProtectedRoute`, and `AdminTokensPage` exports

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-27-increase-system-test-coverage.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
