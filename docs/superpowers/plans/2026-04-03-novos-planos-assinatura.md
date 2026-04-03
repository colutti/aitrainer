# Novos Planos de Assinatura Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidar o produto em `Free`, `Basic` e `Pro`, remover `Premium` das superfícies ativas, implementar os limites/capacidades que ainda não existem e unificar a apresentação de planos entre landing, onboarding e configurações.

**Architecture:** Centralizar no backend um catálogo de capacidades por plano que exponha limites e permissões reais, depois fazer o frontend consumir a mesma semântica com um componente compartilhado de card de plano. O enforcement fica no backend para chat, trainers, integrações, Telegram e importações; a UI apenas reflete, bloqueia e vende upgrade com copy consistente.

**Tech Stack:** FastAPI, Pydantic, Pytest, React 19, TypeScript, Vitest, i18next JSON locales, Stripe.

---

## File Structure / Ownership

- Modify: `backend/src/core/subscription.py`
- Modify: `backend/src/api/models/user_profile.py`
- Modify: `backend/src/api/endpoints/message.py`
- Modify: `backend/src/api/endpoints/trainer.py`
- Modify: `backend/src/api/endpoints/hevy.py`
- Modify: `backend/src/api/endpoints/telegram.py`
- Modify: `backend/src/api/endpoints/nutrition.py`
- Modify: `backend/src/api/endpoints/stripe.py`
- Test: `backend/tests/test_subscription_plan_config.py`
- Test: `backend/tests/api/models/test_user_profile_limits.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`
- Test: `backend/tests/unit/api/test_trainer_endpoints.py`
- Test: `backend/tests/unit/api/test_hevy_endpoints.py`
- Test: `backend/tests/unit/api/test_telegram_endpoints.py`
- Test: `backend/tests/unit/api/test_nutrition_api.py`
- Test: `backend/tests/test_stripe_webhook.py`

- Create: `frontend/src/shared/lib/plan-catalog.ts`
- Create: `frontend/src/shared/components/plans/PlanCard.tsx`
- Create: `frontend/src/shared/components/plans/PlanCard.test.tsx`
- Modify: `frontend/src/shared/constants/stripe.ts`
- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/landing/components/Pricing.test.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.test.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.test.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

---

### Task 1: Centralizar catálogo e capacidades dos planos no backend

**Files:**
- Modify: `backend/src/core/subscription.py`
- Modify: `backend/src/api/models/user_profile.py`
- Test: `backend/tests/test_subscription_plan_config.py`
- Test: `backend/tests/api/models/test_user_profile_limits.py`

- [ ] **Step 1: Escrever os testes falhando para o novo catálogo**

```python
# backend/tests/test_subscription_plan_config.py
from src.core.subscription import (
    SubscriptionPlan,
    SUBSCRIPTION_PLANS,
    can_use_image_input,
    can_use_integrations,
    can_use_telegram,
    can_use_imports,
)


def test_subscription_catalog_exposes_only_free_basic_and_pro():
    assert set(SubscriptionPlan) == {
        SubscriptionPlan.FREE,
        SubscriptionPlan.BASIC,
        SubscriptionPlan.PRO,
    }
    assert set(SUBSCRIPTION_PLANS.keys()) == set(SubscriptionPlan)


def test_free_capabilities_match_trial_strategy():
    free = SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]
    assert free.daily_limit == 20
    assert free.validity_days == 7
    assert free.allowed_trainers == ["gymbro"]
    assert free.image_input_enabled is False
    assert free.integrations_enabled is False
    assert free.telegram_enabled is False
    assert free.imports_enabled is False


def test_basic_and_pro_capabilities_match_product_strategy():
    basic = SUBSCRIPTION_PLANS[SubscriptionPlan.BASIC]
    pro = SUBSCRIPTION_PLANS[SubscriptionPlan.PRO]
    assert basic.monthly_limit == 100
    assert basic.allowed_trainers is None
    assert basic.image_input_enabled is False
    assert basic.integrations_enabled is False
    assert pro.monthly_limit == 300
    assert pro.image_input_enabled is True
    assert pro.integrations_enabled is True
    assert pro.telegram_enabled is True
    assert pro.imports_enabled is True


def test_capability_helpers_follow_catalog():
    assert can_use_image_input("Free") is False
    assert can_use_image_input("Basic") is False
    assert can_use_image_input("Pro") is True
    assert can_use_integrations("Basic") is False
    assert can_use_integrations("Pro") is True
    assert can_use_telegram("Basic") is False
    assert can_use_imports("Pro") is True
```

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/api/models/test_user_profile_limits.py -v`
Expected: FAIL com referências inexistentes a helpers/campos e/ou presença de `Premium`.

- [ ] **Step 3: Implementar o novo modelo de capacidades**

```python
# backend/src/core/subscription.py
class SubscriptionPlan(str, Enum):
    FREE = "Free"
    BASIC = "Basic"
    PRO = "Pro"


class PlanDetails(BaseModel):
    name: str
    monthly_limit: int | None
    total_limit: int | None
    daily_limit: int | None
    validity_days: int | None
    allowed_trainers: list[str] | None
    price_usd: float
    image_input_enabled: bool = False
    integrations_enabled: bool = False
    telegram_enabled: bool = False
    imports_enabled: bool = False
```

- [ ] **Step 4: Definir o catálogo final dos três planos**

```python
# backend/src/core/subscription.py
SUBSCRIPTION_PLANS = {
    SubscriptionPlan.FREE: PlanDetails(
        name="Free",
        monthly_limit=None,
        total_limit=None,
        daily_limit=20,
        validity_days=7,
        allowed_trainers=["gymbro"],
        price_usd=0.0,
    ),
    SubscriptionPlan.BASIC: PlanDetails(
        name="Basic",
        monthly_limit=100,
        total_limit=None,
        daily_limit=None,
        validity_days=None,
        allowed_trainers=None,
        price_usd=4.99,
    ),
    SubscriptionPlan.PRO: PlanDetails(
        name="Pro",
        monthly_limit=300,
        total_limit=None,
        daily_limit=None,
        validity_days=None,
        allowed_trainers=None,
        price_usd=9.99,
        image_input_enabled=True,
        integrations_enabled=True,
        telegram_enabled=True,
        imports_enabled=True,
    ),
}
```

- [ ] **Step 5: Adicionar helpers explícitos de capacidade**

```python
# backend/src/core/subscription.py
def get_plan_details(subscription_plan: str | None) -> PlanDetails:
    try:
        return SUBSCRIPTION_PLANS[SubscriptionPlan(subscription_plan)]
    except (ValueError, TypeError, KeyError):
        return SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]


def can_use_image_input(subscription_plan: str | None) -> bool:
    return get_plan_details(subscription_plan).image_input_enabled


def can_use_integrations(subscription_plan: str | None) -> bool:
    return get_plan_details(subscription_plan).integrations_enabled


def can_use_telegram(subscription_plan: str | None) -> bool:
    return get_plan_details(subscription_plan).telegram_enabled


def can_use_imports(subscription_plan: str | None) -> bool:
    return get_plan_details(subscription_plan).imports_enabled
```

- [ ] **Step 6: Ajustar os testes de limites do `UserProfile` para o novo catálogo**

```python
# backend/tests/api/models/test_user_profile_limits.py
def test_pro_user_limits():
    profile = UserProfile(
        email="pro@test.com",
        gender="Male",
        age=30,
        height=180,
        goal_type="maintain",
        weekly_rate=0.5,
        subscription_plan=SubscriptionPlan.PRO,
    )
    assert profile.current_daily_limit is None
    assert profile.current_plan_limit == 300
```

- [ ] **Step 7: Rodar novamente a suíte do task**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/api/models/test_user_profile_limits.py -v`
Expected: PASS com `Premium` removido e catálogo coerente.

- [ ] **Step 8: Commit**

```bash
git add backend/src/core/subscription.py backend/src/api/models/user_profile.py backend/tests/test_subscription_plan_config.py backend/tests/api/models/test_user_profile_limits.py
git commit -m "feat: centralize new subscription plan capabilities"
```

---

### Task 2: Implementar enforcement backend para chat, trainer, integrações e importações

**Files:**
- Modify: `backend/src/api/endpoints/message.py`
- Modify: `backend/src/api/endpoints/trainer.py`
- Modify: `backend/src/api/endpoints/hevy.py`
- Modify: `backend/src/api/endpoints/telegram.py`
- Modify: `backend/src/api/endpoints/nutrition.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`
- Test: `backend/tests/unit/api/test_trainer_endpoints.py`
- Test: `backend/tests/unit/api/test_hevy_endpoints.py`
- Test: `backend/tests/unit/api/test_telegram_endpoints.py`
- Test: `backend/tests/unit/api/test_nutrition_api.py`

- [ ] **Step 1: Escrever testes falhando para imagem apenas no `Pro`**

```python
# backend/tests/unit/api/test_message_endpoints.py
def test_message_ai_rejects_images_for_basic_plan(...):
    mock_profile.subscription_plan = "Basic"
    response = client.post(
        "/message/ai",
        json={"user_message": "analisar", "images": ["data:image/png;base64,abc"]},
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "IMAGE_NOT_ALLOWED_FOR_PLAN"
```

- [ ] **Step 2: Escrever testes falhando para gates de trainer e integrações**

```python
# backend/tests/unit/api/test_trainer_endpoints.py
def test_free_user_cannot_select_locked_trainer(...):
    mock_user.subscription_plan = "Free"
    response = client.put("/trainer/update_trainer_profile", json={"trainer_type": "atlas"})
    assert response.status_code == 403


# backend/tests/unit/api/test_hevy_endpoints.py
def test_basic_user_cannot_open_hevy_config(...):
    profile.subscription_plan = "Basic"
    response = client.post("/integrations/hevy/config", json={"api_key": "abc", "enabled": True})
    assert response.status_code == 403
    assert response.json()["detail"] == "INTEGRATION_NOT_ALLOWED_FOR_PLAN"


# backend/tests/unit/api/test_telegram_endpoints.py
def test_basic_user_cannot_generate_telegram_code(...):
    profile.subscription_plan = "Basic"
    response = client.post("/telegram/generate-code")
    assert response.status_code == 403
```

- [ ] **Step 3: Escrever teste falhando para importação de MyFitnessPal apenas no `Pro`**

```python
# backend/tests/unit/api/test_nutrition_api.py
def test_basic_user_cannot_import_myfitnesspal_csv(...):
    profile.subscription_plan = "Basic"
    response = client.post(
        "/nutrition/import/myfitnesspal",
        files={"file": ("export.csv", b"Date,Calories\n2026-04-01,2000", "text/csv")},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "IMPORT_NOT_ALLOWED_FOR_PLAN"
```

- [ ] **Step 4: Rodar os testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/unit/api/test_message_endpoints.py tests/unit/api/test_trainer_endpoints.py tests/unit/api/test_hevy_endpoints.py tests/unit/api/test_telegram_endpoints.py tests/unit/api/test_nutrition_api.py -v`
Expected: FAIL porque os endpoints ainda não verificam essas capacidades.

- [ ] **Step 5: Aplicar gate no endpoint de mensagem**

```python
# backend/src/api/endpoints/message.py
from src.core.subscription import can_use_image_input

if message.images and not can_use_image_input(profile.subscription_plan):
    raise HTTPException(status_code=403, detail="IMAGE_NOT_ALLOWED_FOR_PLAN")
```

- [ ] **Step 6: Aplicar gate em Hevy, Telegram e importações**

```python
# backend/src/api/endpoints/hevy.py
from src.core.subscription import can_use_integrations

if not can_use_integrations(profile.subscription_plan):
    raise HTTPException(status_code=403, detail="INTEGRATION_NOT_ALLOWED_FOR_PLAN")


# backend/src/api/endpoints/telegram.py
from src.core.subscription import can_use_telegram

profile = brain.get_user_profile(user_email)
if not profile or not can_use_telegram(profile.subscription_plan):
    raise HTTPException(status_code=403, detail="TELEGRAM_NOT_ALLOWED_FOR_PLAN")


# backend/src/api/endpoints/nutrition.py
from src.core.subscription import can_use_imports

profile = db.get_user_profile(user_email)
if not profile or not can_use_imports(profile.subscription_plan):
    raise HTTPException(status_code=403, detail="IMPORT_NOT_ALLOWED_FOR_PLAN")
```

- [ ] **Step 7: Manter a validação de trainer baseada no catálogo**

```python
# backend/src/api/endpoints/trainer.py
plan_details = get_plan_details(user_profile.subscription_plan)
allowed = plan_details.allowed_trainers
if allowed and profile_input.trainer_type not in allowed:
    raise HTTPException(
        status_code=403,
        detail=f"Trainer '{profile_input.trainer_type}' is not available in the {plan_details.name} plan",
    )
```

- [ ] **Step 8: Rodar novamente os testes do task**

Run: `cd backend && .venv/bin/pytest tests/unit/api/test_message_endpoints.py tests/unit/api/test_trainer_endpoints.py tests/unit/api/test_hevy_endpoints.py tests/unit/api/test_telegram_endpoints.py tests/unit/api/test_nutrition_api.py -v`
Expected: PASS com todos os bloqueios aplicados.

- [ ] **Step 9: Commit**

```bash
git add backend/src/api/endpoints/message.py backend/src/api/endpoints/trainer.py backend/src/api/endpoints/hevy.py backend/src/api/endpoints/telegram.py backend/src/api/endpoints/nutrition.py backend/tests/unit/api/test_message_endpoints.py backend/tests/unit/api/test_trainer_endpoints.py backend/tests/unit/api/test_hevy_endpoints.py backend/tests/unit/api/test_telegram_endpoints.py backend/tests/unit/api/test_nutrition_api.py
git commit -m "feat: enforce subscription capabilities across backend endpoints"
```

---

### Task 3: Remover `Premium` do fluxo Stripe e da leitura de planos pagos

**Files:**
- Modify: `backend/src/api/endpoints/stripe.py`
- Modify: `frontend/src/shared/constants/stripe.ts`
- Test: `backend/tests/test_stripe_webhook.py`

- [ ] **Step 1: Escrever testes falhando para o novo catálogo Stripe**

```python
# backend/tests/test_stripe_webhook.py
def test_get_subscription_plan_maps_basic_and_pro_only(settings_module):
    basic = {"status": "active", "items": {"data": [{"price": {"id": settings_module.STRIPE_PRICE_ID_BASIC}}]}}
    pro = {"status": "active", "items": {"data": [{"price": {"id": settings_module.STRIPE_PRICE_ID_PRO}}]}}
    assert _get_subscription_plan(basic) == "Basic"
    assert _get_subscription_plan(pro) == "Pro"


def test_get_subscription_plan_falls_back_to_free_for_unknown_price(settings_module):
    unknown = {"status": "active", "items": {"data": [{"price": {"id": "price_unknown"}}]}}
    assert _get_subscription_plan(unknown) == "Free"
```

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/test_stripe_webhook.py -k subscription_plan -v`
Expected: FAIL se houver expectativa ou mapeamento residual de `Premium`.

- [ ] **Step 3: Simplificar o mapeamento Stripe no backend**

```python
# backend/src/api/endpoints/stripe.py
def _get_subscription_plan(subscription):
    status = subscription.get("status")
    if status not in ["active", "trialing"]:
        return "Free"

    items = subscription.get("items", {}).get("data", [])
    if not items:
        return "Free"

    price_id = items[0]["price"]["id"]
    if price_id == settings.STRIPE_PRICE_ID_BASIC:
        return "Basic"
    if price_id == settings.STRIPE_PRICE_ID_PRO:
        return "Pro"
    return "Free"
```

- [ ] **Step 4: Remover `premium` do frontend**

```ts
// frontend/src/shared/constants/stripe.ts
export const STRIPE_PRICE_IDS = {
  basic: 'price_1TAPTBPTisrIM5tN5Dz3P2en',
  pro: 'price_1TAPTBPTisrIM5tNKY7Nxw3i',
} as const;
```

- [ ] **Step 5: Rodar os testes do task**

Run: `cd backend && .venv/bin/pytest tests/test_stripe_webhook.py -v`
Expected: PASS com mapeamento restrito a `Basic` e `Pro`.

- [ ] **Step 6: Commit**

```bash
git add backend/src/api/endpoints/stripe.py backend/tests/test_stripe_webhook.py frontend/src/shared/constants/stripe.ts
git commit -m "refactor: remove premium from stripe plan mapping"
```

---

### Task 4: Criar catálogo e card compartilhado de planos no frontend

**Files:**
- Create: `frontend/src/shared/lib/plan-catalog.ts`
- Create: `frontend/src/shared/components/plans/PlanCard.tsx`
- Create: `frontend/src/shared/components/plans/PlanCard.test.tsx`

- [ ] **Step 1: Escrever teste falhando para o catálogo de frontend**

```tsx
// frontend/src/shared/components/plans/PlanCard.test.tsx
import { render, screen } from '@testing-library/react';
import { PlanCard } from './PlanCard';

it('renders Free, Basic and Pro plan features consistently', () => {
  render(
    <PlanCard
      plan={{
        id: 'pro',
        name: 'Pro',
        priceLabel: '$9.99',
        subtitle: 'A experiência completa com dados, fotos e automações.',
        features: ['300 mensagens por mês', 'Fotos no chat'],
      }}
      context="marketing"
      actionLabel="Assinar Pro"
      onAction={() => {}}
    />,
  );

  expect(screen.getByText('Pro')).toBeInTheDocument();
  expect(screen.getByText('300 mensagens por mês')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Assinar Pro' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Rodar o teste e confirmar falha**

Run: `cd frontend && npm test -- PlanCard.test.tsx`
Expected: FAIL porque o componente e o catálogo ainda não existem.

- [ ] **Step 3: Criar um catálogo compartilhado para as três superfícies**

```ts
// frontend/src/shared/lib/plan-catalog.ts
export type PlanCatalogEntry = {
  id: 'free' | 'basic' | 'pro';
  nameKey: string;
  subtitleKey: string;
  featureKeys: string[];
  badgeKey?: string;
  highlight?: boolean;
};

export const PLAN_CATALOG: PlanCatalogEntry[] = [
  {
    id: 'free',
    nameKey: 'landing.plans.items.free.name',
    subtitleKey: 'landing.plans.items.free.description',
    featureKeys: [
      'landing.plans.items.free.features.0',
      'landing.plans.items.free.features.1',
      'landing.plans.items.free.features.2',
      'landing.plans.items.free.features.3',
    ],
  },
  {
    id: 'basic',
    nameKey: 'landing.plans.items.basic.name',
    subtitleKey: 'landing.plans.items.basic.description',
    featureKeys: [
      'landing.plans.items.basic.features.0',
      'landing.plans.items.basic.features.1',
      'landing.plans.items.basic.features.2',
      'landing.plans.items.basic.features.3',
    ],
  },
  {
    id: 'pro',
    nameKey: 'landing.plans.items.pro.name',
    subtitleKey: 'landing.plans.items.pro.description',
    featureKeys: [
      'landing.plans.items.pro.features.0',
      'landing.plans.items.pro.features.1',
      'landing.plans.items.pro.features.2',
      'landing.plans.items.pro.features.3',
    ],
    highlight: true,
    badgeKey: 'landing.plans.recommended',
  },
];
```

- [ ] **Step 4: Criar o card reutilizável**

```tsx
// frontend/src/shared/components/plans/PlanCard.tsx
type PlanCardProps = {
  plan: {
    id: string;
    name: string;
    priceLabel: string;
    subtitle: string;
    features: string[];
    badge?: string;
    highlight?: boolean;
  };
  context: 'marketing' | 'selection' | 'management';
  actionLabel?: string;
  selected?: boolean;
  current?: boolean;
  disabled?: boolean;
  onAction?: () => void;
};
```

- [ ] **Step 5: Garantir que o card aceite diferenças de contexto sem duplicar markup**

```tsx
// frontend/src/shared/components/plans/PlanCard.tsx
{plan.badge ? <span>{plan.badge}</span> : null}
{current ? <span>{t('settings.subscription.active')}</span> : null}
<button disabled={disabled} onClick={onAction}>
  {actionLabel}
</button>
```

- [ ] **Step 6: Rodar os testes do task**

Run: `cd frontend && npm test -- PlanCard.test.tsx`
Expected: PASS com o card renderizando features e CTA.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/shared/lib/plan-catalog.ts frontend/src/shared/components/plans/PlanCard.tsx frontend/src/shared/components/plans/PlanCard.test.tsx
git commit -m "feat: add shared plan catalog and reusable plan card"
```

---

### Task 5: Reescrever landing, assinatura e onboarding para usar o card compartilhado

**Files:**
- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/landing/components/Pricing.test.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.test.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionView.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.test.tsx`

- [ ] **Step 1: Escrever testes falhando para ausência de `Premium` e presença dos três planos**

```tsx
// frontend/src/features/landing/components/Pricing.test.tsx
it('shows only Free, Basic and Pro plans', () => {
  render(<Pricing />);
  expect(screen.getByText(/Free/i)).toBeInTheDocument();
  expect(screen.getByText(/Basic/i)).toBeInTheDocument();
  expect(screen.getByText(/Pro/i)).toBeInTheDocument();
  expect(screen.queryByText(/Premium/i)).not.toBeInTheDocument();
});


// frontend/src/features/settings/components/SubscriptionPage.test.tsx
it('builds subscription options from the shared three-plan catalog', async () => {
  render(<SubscriptionPage />);
  await screen.findByText('free');
  expect(screen.queryByText(/premium/i)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Escrever teste falhando para onboarding com três planos**

```tsx
// frontend/src/features/onboarding/components/OnboardingView.test.tsx
it('renders only Free, Basic and Pro on the plan step', () => {
  render(<OnboardingView step={3} {...defaultProps} />);
  expect(screen.getByText('Free')).toBeInTheDocument();
  expect(screen.getByText('Basic')).toBeInTheDocument();
  expect(screen.getByText('Pro')).toBeInTheDocument();
  expect(screen.queryByText('Premium')).not.toBeInTheDocument();
});
```

- [ ] **Step 3: Rodar os testes e confirmar falha**

Run: `cd frontend && npm test -- Pricing.test.tsx SubscriptionPage.test.tsx OnboardingView.test.tsx`
Expected: FAIL porque as telas ainda renderizam `Premium` e usam estruturas separadas.

- [ ] **Step 4: Fazer a landing consumir o catálogo compartilhado**

```tsx
// frontend/src/features/landing/components/Pricing.tsx
import { PLAN_CATALOG } from '@shared/lib/plan-catalog';
import { PlanCard } from '@shared/components/plans/PlanCard';

{PLAN_CATALOG.map((entry) => (
  <PlanCard
    key={entry.id}
    context="marketing"
    plan={buildPlanCardModel(entry, t, isPt)}
    actionLabel={t(`landing.plans.items.${entry.id}.button`)}
    onAction={() => { void handleSubscribe(entry.id); }}
  />
))}
```

- [ ] **Step 5: Fazer assinatura e onboarding consumirem o mesmo card**

```tsx
// frontend/src/features/settings/components/SubscriptionPage.tsx
const plans = PLAN_CATALOG.map((entry) => buildPlanCardModel(entry, t, isPt));


// frontend/src/features/onboarding/components/OnboardingView.tsx
{PLAN_CATALOG.map((entry) => (
  <PlanCard
    key={entry.id}
    context="selection"
    plan={buildPlanCardModel(entry, t, isPt)}
    selected={formData.subscription_plan?.toLowerCase() === entry.id}
    actionLabel={t('common.next')}
    onAction={() => setFormData({ ...formData, subscription_plan: normalizePlanName(entry.id) })}
  />
))}
```

- [ ] **Step 6: Simplificar `SubscriptionView` para não conhecer planos hardcoded**

```tsx
// frontend/src/features/settings/components/SubscriptionView.tsx
const PLAN_PRIORITY: Record<string, number> = { free: 0, basic: 1, pro: 2 };
```

- [ ] **Step 7: Rodar novamente os testes do task**

Run: `cd frontend && npm test -- Pricing.test.tsx SubscriptionPage.test.tsx OnboardingView.test.tsx`
Expected: PASS com o catálogo único de três planos.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/landing/components/Pricing.tsx frontend/src/features/landing/components/Pricing.test.tsx frontend/src/features/settings/components/SubscriptionPage.tsx frontend/src/features/settings/components/SubscriptionPage.test.tsx frontend/src/features/settings/components/SubscriptionView.tsx frontend/src/features/onboarding/components/OnboardingView.tsx frontend/src/features/onboarding/components/OnboardingView.test.tsx
git commit -m "refactor: reuse shared plan cards across pricing flows"
```

---

### Task 6: Bloquear a aba de integrações fora do `Pro` e alinhar copy/i18n

**Files:**
- Modify: `frontend/src/features/settings/components/IntegrationsView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

- [ ] **Step 1: Escrever teste falhando para estado bloqueado no `Basic`**

```tsx
// frontend/src/features/settings/components/IntegrationsView.test.tsx
it('shows upgrade messaging when integrations are not allowed for the plan', () => {
  render(
    <IntegrationsView
      planCapabilities={{ integrationsEnabled: false, telegramEnabled: false, importsEnabled: false }}
      hevy={{ ...defaultHevy }}
      telegram={{ ...defaultTelegram }}
      imports={{ ...defaultImports }}
    />,
  );

  expect(screen.getAllByText(/Disponível no Pro/i).length).toBeGreaterThan(0);
  expect(screen.queryByRole('button', { name: /Gerar Código/i })).not.toBeEnabled();
});
```

- [ ] **Step 2: Rodar o teste e confirmar falha**

Run: `cd frontend && npm test -- IntegrationsView.test.tsx`
Expected: FAIL porque a view ainda assume disponibilidade universal.

- [ ] **Step 3: Passar capacidades do plano para `IntegrationsView`**

```tsx
// frontend/src/features/settings/components/IntegrationsView.tsx
export interface IntegrationsViewProps {
  planCapabilities?: {
    integrationsEnabled: boolean;
    telegramEnabled: boolean;
    importsEnabled: boolean;
  };
  ...
}
```

- [ ] **Step 4: Renderizar estados bloqueados para `Free` e `Basic`**

```tsx
// frontend/src/features/settings/components/IntegrationsView.tsx
const integrationsEnabled = planCapabilities?.integrationsEnabled ?? true;
const telegramEnabled = planCapabilities?.telegramEnabled ?? true;
const importsEnabled = planCapabilities?.importsEnabled ?? true;

if (!integrationsEnabled) {
  return <p>{t('settings.integrations.pro_only')}</p>;
}
```

- [ ] **Step 5: Traduzir a nova copy nos três locales**

```json
// frontend/src/locales/pt-BR.json
"integrations": {
  "pro_only": "Disponível no Pro",
  "pro_only_desc": "Faça upgrade para conectar apps e automatizar sua rotina."
}
```

- [ ] **Step 6: Rodar os testes do task**

Run: `cd frontend && npm test -- IntegrationsView.test.tsx`
Expected: PASS com estados bloqueados e CTA coerente.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/settings/components/IntegrationsView.tsx frontend/src/features/settings/components/IntegrationsView.test.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json
git commit -m "feat: gate integrations UI by subscription capabilities"
```

---

### Task 7: Validar a stack inteira tocada pela mudança

**Files:**
- No new files

- [ ] **Step 1: Rodar a suíte backend focada nas áreas alteradas**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/api/models/test_user_profile_limits.py tests/unit/api/test_message_endpoints.py tests/unit/api/test_trainer_endpoints.py tests/unit/api/test_hevy_endpoints.py tests/unit/api/test_telegram_endpoints.py tests/unit/api/test_nutrition_api.py tests/test_stripe_webhook.py -v`
Expected: PASS com gates de plano, Stripe e limites atualizados.

- [ ] **Step 2: Rodar lint e análise estática do backend**

Run: `cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src`
Expected: PASS sem warnings novos nos arquivos tocados.

- [ ] **Step 3: Rodar a suíte frontend focada nas áreas alteradas**

Run: `cd frontend && npm test -- PlanCard.test.tsx Pricing.test.tsx SubscriptionPage.test.tsx OnboardingView.test.tsx IntegrationsView.test.tsx`
Expected: PASS com renderização unificada dos planos e bloqueios da UI.

- [ ] **Step 4: Rodar lint e typecheck do frontend**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS sem erros.

- [ ] **Step 5: Rodar verificação integrada oficial se o branch estiver pronto para fechamento**

Run: `make verify`
Expected: PASS nas verificações rápidas oficiais do repositório.

- [ ] **Step 6: Commit final**

```bash
git add backend frontend
git commit -m "feat: ship new subscription plans across app surfaces"
```

