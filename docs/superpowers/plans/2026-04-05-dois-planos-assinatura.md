# Dois Planos de Assinatura Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrar a FityQ para apenas `Grátis` e `Pro`, com trial de 7 dias do `Pro`, enforcement completo no backend, `gemini-2.5-flash-lite` como modelo padrão, preço cheio `6.99`, promoção `4.99` e Stripe/frontend alinhados.

**Architecture:** O backend passa a calcular capacidades efetivas a partir de `subscription_plan + trial_ends_at + counters do ciclo`, e o frontend deixa de inferir permissões por strings soltas. Stripe fica com um único plano pago recorrente, com preços reais por moeda e catálogo visual compartilhado entre landing, onboarding e configurações.

**Tech Stack:** FastAPI, Pydantic, Pytest, React 19, TypeScript, Vitest, i18next, Stripe Checkout/Portal, MongoDB.

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
- Modify: `backend/src/core/config.py`
- Modify: `backend/src/services/trainer.py`
- Test: `backend/tests/test_subscription_plan_config.py`
- Test: `backend/tests/api/models/test_user_profile_limits.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`
- Test: `backend/tests/unit/api/test_trainer_endpoints.py`
- Test: `backend/tests/unit/api/test_hevy_endpoints.py`
- Test: `backend/tests/unit/api/test_telegram_endpoints.py`
- Test: `backend/tests/unit/api/test_nutrition_api.py`
- Test: `backend/tests/test_stripe_webhook.py`

- Modify: `frontend/src/shared/constants/plan-catalog.ts`
- Modify: `frontend/src/shared/constants/stripe.ts`
- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/landing/components/Pricing.test.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionView.tsx`
- Modify: `frontend/src/features/settings/components/TrainerSettingsPage.tsx`
- Modify: `frontend/src/features/settings/components/TrainerSettingsView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsPage.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingPage.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`
- Test: `frontend/src/features/settings/components/SubscriptionView.test.tsx`
- Test: `frontend/src/features/settings/components/TrainerSettingsPage.test.tsx`
- Test: `frontend/src/features/settings/components/IntegrationsView.test.tsx`
- Test: `frontend/src/features/onboarding/components/OnboardingView.test.tsx`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`

- Modify: `backend-admin/src/api/endpoints/admin_users.py`
- Modify: `frontend/admin/src/types/admin-api.ts`
- Test: `backend-admin/tests/test_admin_users.py`

---

### Task 1: Redesenhar o modelo de assinatura e trial no backend

**Files:**
- Modify: `backend/src/core/subscription.py`
- Modify: `backend/src/api/models/user_profile.py`
- Test: `backend/tests/test_subscription_plan_config.py`
- Test: `backend/tests/api/models/test_user_profile_limits.py`

- [ ] **Step 1: Escrever testes falhando para o novo catálogo**

Validar:
- só existem `Free` e `Pro`
- `Free` tem `7` dias de trial via capacidade efetiva, não via plano pago separado
- `Pro` tem `500` mensagens por ciclo
- `Pro` tem `15` fotos por ciclo
- `Free` pós-trial não pode conversar nem enviar imagem

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/api/models/test_user_profile_limits.py -v`
Expected: FAIL porque o catálogo atual ainda conhece `Basic`, não conhece fotos por ciclo e não separa trial de capacidade efetiva.

- [ ] **Step 3: Atualizar o catálogo em `subscription.py`**

Implementar:
- `SubscriptionPlan.FREE`
- `SubscriptionPlan.PRO`
- `monthly_message_limit`
- `monthly_photo_limit`
- `allowed_trainers`
- `telegram_enabled`
- `integrations_enabled`
- `imports_enabled`
- `chat_enabled`
- helper para calcular capacidades efetivas considerando `trial_ends_at`

- [ ] **Step 4: Atualizar `UserProfile`**

Adicionar ou revisar campos:
- `trial_ends_at`
- `photos_sent_this_month`
- `current_billing_cycle_start`
- `messages_sent_this_month`
- computed fields para:
  - `is_trial_active`
  - `effective_plan_name`
  - `effective_chat_enabled`
  - `effective_remaining_messages`
  - `effective_remaining_photos`

- [ ] **Step 5: Rodar novamente os testes do task**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/api/models/test_user_profile_limits.py -v`
Expected: PASS com o novo catálogo e capacidades efetivas.

- [ ] **Step 6: Commit**

```bash
git add backend/src/core/subscription.py backend/src/api/models/user_profile.py backend/tests/test_subscription_plan_config.py backend/tests/api/models/test_user_profile_limits.py
git commit -m "feat: model free and pro capabilities with trial"
```

### Task 2: Enforce backend para chat, fotos, trainer, Telegram, integrações e imports

**Files:**
- Modify: `backend/src/api/endpoints/message.py`
- Modify: `backend/src/api/endpoints/trainer.py`
- Modify: `backend/src/api/endpoints/hevy.py`
- Modify: `backend/src/api/endpoints/telegram.py`
- Modify: `backend/src/api/endpoints/nutrition.py`
- Modify: `backend/src/services/trainer.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`
- Test: `backend/tests/unit/api/test_trainer_endpoints.py`
- Test: `backend/tests/unit/api/test_hevy_endpoints.py`
- Test: `backend/tests/unit/api/test_telegram_endpoints.py`
- Test: `backend/tests/unit/api/test_nutrition_api.py`

- [ ] **Step 1: Escrever testes falhando para o enforcement**

Cobrir:
- `Free` com trial ativo pode conversar e enviar fotos
- `Free` pós-trial recebe bloqueio ao mandar mensagem
- `Free` pós-trial recebe bloqueio ao enviar imagem
- `Free` pós-trial só pode permanecer no `gymbro`
- `Free` pós-trial recebe bloqueio em Telegram
- `Free` pós-trial recebe bloqueio em Hevy/imports
- `Pro` respeita `500` mensagens e `15` fotos por ciclo

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/unit/api/test_message_endpoints.py tests/unit/api/test_trainer_endpoints.py tests/unit/api/test_hevy_endpoints.py tests/unit/api/test_telegram_endpoints.py tests/unit/api/test_nutrition_api.py -v`
Expected: FAIL com regras antigas de `Basic/Pro` e ausência de limite mensal de fotos.

- [ ] **Step 3: Implementar bloqueio de mensagem e foto**

Em `message.py` e `trainer.py`:
- usar capacidades efetivas
- bloquear `chat_enabled = False`
- contar foto no ciclo
- retornar erros explícitos para paywall

- [ ] **Step 4: Implementar bloqueio de trainer e reset para Breno**

Em `trainer.py`:
- qualquer `Free` pós-trial fora de `gymbro` deve ser resetado
- seleção de outro trainer deve retornar erro de permissão/capacidade

- [ ] **Step 5: Implementar bloqueio de Telegram, integrações e importações**

Em `hevy.py`, `telegram.py` e `nutrition.py`:
- usar helper central de capacidades
- bloquear endpoints fora de trial/`Pro`

- [ ] **Step 6: Rodar novamente a suíte do task**

Run: `cd backend && .venv/bin/pytest tests/unit/api/test_message_endpoints.py tests/unit/api/test_trainer_endpoints.py tests/unit/api/test_hevy_endpoints.py tests/unit/api/test_telegram_endpoints.py tests/unit/api/test_nutrition_api.py -v`
Expected: PASS com enforcement completo.

- [ ] **Step 7: Commit**

```bash
git add backend/src/api/endpoints/message.py backend/src/api/endpoints/trainer.py backend/src/api/endpoints/hevy.py backend/src/api/endpoints/telegram.py backend/src/api/endpoints/nutrition.py backend/src/services/trainer.py backend/tests/unit/api/test_message_endpoints.py backend/tests/unit/api/test_trainer_endpoints.py backend/tests/unit/api/test_hevy_endpoints.py backend/tests/unit/api/test_telegram_endpoints.py backend/tests/unit/api/test_nutrition_api.py
git commit -m "feat: enforce free and pro plan restrictions"
```

### Task 3: Ajustar Stripe, ciclo de cobrança, preços e migração comercial

**Files:**
- Modify: `backend/src/api/endpoints/stripe.py`
- Modify: `backend/src/core/config.py`
- Test: `backend/tests/test_stripe_webhook.py`

- [ ] **Step 1: Escrever testes falhando para o novo fluxo Stripe**

Cobrir:
- webhook só reconhece `Free` e `Pro`
- reset de mensagens e fotos no início do ciclo
- downgrade para `Free` reseta trainer para `gymbro`
- suporte a múltiplos `price_id` por moeda para o mesmo `Pro`

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/test_stripe_webhook.py -v`
Expected: FAIL porque o webhook ainda conhece `Basic` e não reseta fotos.

- [ ] **Step 3: Atualizar a configuração Stripe**

Em `config.py`:
- remover dependência ativa de `STRIPE_PRICE_ID_BASIC`
- remover dependência ativa de `STRIPE_PRICE_ID_PREMIUM`
- introduzir estrutura para `STRIPE_PRICE_ID_PRO_*` por moeda ou mapa serializado por env

- [ ] **Step 4: Atualizar `stripe.py`**

Implementar:
- mapeamento de todos os `price_id` válidos para `Pro`
- reset de `messages_sent_this_month`
- reset de `photos_sent_this_month`
- manutenção de `current_billing_cycle_start`
- downgrade limpo para `Free`

- [ ] **Step 5: Definir a estratégia promocional do Stripe**

Escolha operacional recomendada:
- criar `price_id` promocional real de `4.99` por moeda
- manter `6.99` apenas como preço cheio visual no frontend por enquanto

Registrar no código e na doc que:
- o checkout cobra `4.99`
- o preço cheio é de marketing

- [ ] **Step 6: Rodar novamente os testes do task**

Run: `cd backend && .venv/bin/pytest tests/test_stripe_webhook.py -v`
Expected: PASS com suporte ao novo catálogo e reset por ciclo.

- [ ] **Step 7: Commit**

```bash
git add backend/src/api/endpoints/stripe.py backend/src/core/config.py backend/tests/test_stripe_webhook.py
git commit -m "feat: align stripe billing with new pro pricing"
```

### Task 4: Unificar catálogo e pricing no frontend principal

**Files:**
- Modify: `frontend/src/shared/constants/plan-catalog.ts`
- Modify: `frontend/src/shared/constants/stripe.ts`
- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionPage.tsx`
- Modify: `frontend/src/features/settings/components/SubscriptionView.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingPage.tsx`
- Modify: `frontend/src/features/onboarding/components/OnboardingView.tsx`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`
- Test: `frontend/src/features/settings/components/SubscriptionView.test.tsx`
- Test: `frontend/src/features/onboarding/components/OnboardingView.test.tsx`

- [ ] **Step 1: Escrever testes falhando para o novo catálogo visual**

Cobrir:
- só existem `free` e `pro`
- `pro` mostra preço cheio `6.99` riscado e preço promocional `4.99`
- `free` comunica trial de `7 dias`
- onboarding, landing e settings usam o mesmo catálogo

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd frontend && npm test -- Pricing.test.tsx SubscriptionView.test.tsx OnboardingView.test.tsx`
Expected: FAIL porque hoje ainda há `basic` e preços hardcoded antigos.

- [ ] **Step 3: Atualizar o catálogo compartilhado**

Em `plan-catalog.ts`:
- remover `basic`
- incluir metadados:
  - `fullPrice`
  - `promoPrice`
  - `promoBadge`
  - `trialCopy`
  - features de `Free` e `Pro`

- [ ] **Step 4: Atualizar landing e assinatura**

Em `Pricing.tsx` e `SubscriptionView.tsx`:
- renderizar preço cheio riscado
- renderizar preço promocional
- destacar o `Pro`
- mostrar explicação de trial no `Grátis`

- [ ] **Step 5: Atualizar onboarding**

Em `OnboardingPage.tsx` e `OnboardingView.tsx`:
- remover `Basic`
- explicar `7 dias de Pro`
- refletir bloqueio de trainer pós-trial apenas como regra de produto, não como escolha de três planos

- [ ] **Step 6: Atualizar `stripe.ts`**

Fazer o frontend selecionar:
- `price_id` correto do `Pro` por moeda/locale
- somente um plano pago no checkout

- [ ] **Step 7: Rodar novamente os testes do task**

Run: `cd frontend && npm test -- Pricing.test.tsx SubscriptionView.test.tsx OnboardingView.test.tsx`
Expected: PASS com duas ofertas e preço promocional consistente.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/shared/constants/plan-catalog.ts frontend/src/shared/constants/stripe.ts frontend/src/features/landing/components/Pricing.tsx frontend/src/features/settings/components/SubscriptionPage.tsx frontend/src/features/settings/components/SubscriptionView.tsx frontend/src/features/onboarding/components/OnboardingPage.tsx frontend/src/features/onboarding/components/OnboardingView.tsx frontend/src/features/landing/components/Pricing.test.tsx frontend/src/features/settings/components/SubscriptionView.test.tsx frontend/src/features/onboarding/components/OnboardingView.test.tsx
git commit -m "feat: update frontend pricing to free and pro only"
```

### Task 5: Ajustar paywalls contextuais de trainer, integrações e chat

**Files:**
- Modify: `frontend/src/features/settings/components/TrainerSettingsPage.tsx`
- Modify: `frontend/src/features/settings/components/TrainerSettingsView.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsPage.tsx`
- Modify: `frontend/src/features/settings/components/IntegrationsView.tsx`
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Test: `frontend/src/features/settings/components/TrainerSettingsPage.test.tsx`
- Test: `frontend/src/features/settings/components/IntegrationsView.test.tsx`

- [ ] **Step 1: Escrever testes falhando para o novo paywall**

Cobrir:
- `Free` em trial não vê bloqueio
- `Free` pós-trial vê trainer bloqueado fora de `gymbro`
- `Free` pós-trial vê integrações bloqueadas
- `Free` pós-trial vê CTA de upgrade no chat ao tentar usar recursos pagos

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd frontend && npm test -- TrainerSettingsPage.test.tsx IntegrationsView.test.tsx`
Expected: FAIL com a semântica antiga baseada em `Free`/`Basic`/`Pro`.

- [ ] **Step 3: Atualizar views para usar capacidades efetivas**

Implementar leitura de:
- `is_trial_active`
- `effective_remaining_messages`
- `effective_remaining_photos`
- `can_use_integrations`
- `can_use_telegram`
- `allowed_trainers`

- [ ] **Step 4: Rodar novamente os testes do task**

Run: `cd frontend && npm test -- TrainerSettingsPage.test.tsx IntegrationsView.test.tsx`
Expected: PASS com paywall contextual correto.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/settings/components/TrainerSettingsPage.tsx frontend/src/features/settings/components/TrainerSettingsView.tsx frontend/src/features/settings/components/IntegrationsPage.tsx frontend/src/features/settings/components/IntegrationsView.tsx frontend/src/features/chat/components/ChatView.tsx frontend/src/features/settings/components/TrainerSettingsPage.test.tsx frontend/src/features/settings/components/IntegrationsView.test.tsx
git commit -m "feat: add contextual paywalls for free users"
```

### Task 6: Atualizar admin e traduções

**Files:**
- Modify: `backend-admin/src/api/endpoints/admin_users.py`
- Modify: `frontend/admin/src/types/admin-api.ts`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`
- Test: `backend-admin/tests/test_admin_users.py`

- [ ] **Step 1: Escrever testes falhando para admin**

Cobrir:
- admin não oferece mais `Basic`
- reset de contadores inclui mensagens e fotos quando plano muda
- trial pode ser ajustado manualmente sem quebrar o novo modelo

- [ ] **Step 2: Rodar os testes e confirmar falha**

Run: `cd backend-admin && .venv/bin/pytest tests/test_admin_users.py -v`
Expected: FAIL com semântica antiga.

- [ ] **Step 3: Atualizar admin users**

Ajustar:
- campos aceitos para `subscription_plan`
- lógica de reset
- serialização dos novos campos

- [ ] **Step 4: Traduzir todas as novas copies**

Atualizar `pt-BR`, `en-US`, `es-ES` para:
- trial de 7 dias
- preço cheio e promocional
- paywall do `Grátis`
- trainer Breno
- Telegram/integrações/fotos/mensagens

- [ ] **Step 5: Rodar novamente os testes do task**

Run: `cd backend-admin && .venv/bin/pytest tests/test_admin_users.py -v`
Expected: PASS com admin coerente.

- [ ] **Step 6: Commit**

```bash
git add backend-admin/src/api/endpoints/admin_users.py frontend/admin/src/types/admin-api.ts frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json backend-admin/tests/test_admin_users.py
git commit -m "feat: align admin and translations with new plans"
```

### Task 7: Verificação final e validação sistêmica

**Files:**
- No new files

- [ ] **Step 1: Rodar verificação backend**

Run: `cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src`
Expected: PASS sem warnings nos arquivos tocados.

- [ ] **Step 2: Rodar verificação frontend**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS.

- [ ] **Step 3: Rodar verificação backend-admin se tocado**

Run: `cd backend-admin && .venv/bin/pylint src && .venv/bin/pyright src`
Expected: PASS.

- [ ] **Step 4: Rodar suíte oficial**

Run: `make test-once`
Expected: PASS com backend, frontend, admin e e2e no fluxo containerizado oficial.

- [ ] **Step 5: Consolidar casos manuais residuais**

Validar manualmente apenas o que for difícil de automatizar:
- checkout Stripe promocional por moeda
- exibição do preço cheio riscado e preço promocional nas três superfícies
- downgrade real pelo portal Stripe
- comportamento do trial vencendo em conta real

- [ ] **Step 6: Commit final**

```bash
git add docs/superpowers/specs/2026-04-05-dois-planos-assinatura-design.md docs/superpowers/plans/2026-04-05-dois-planos-assinatura.md
git commit -m "docs: add two-plan subscription design and implementation plan"
```

---

## Self-Review

- Cobertura de spec:
  - dois planos, trial, enforcement, Stripe, frontend, moedas, modelo padrão e migração estão cobertos.
- Placeholders:
  - não há `TODO`/`TBD`; decisões abertas foram resolvidas com recomendação operacional explícita.
- Consistência:
  - o plano assume `gemini-2.5-flash-lite`, `Free` + `Pro`, trial de `7 dias`, preço cheio `6.99`, preço promocional `4.99`.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-05-dois-planos-assinatura.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
