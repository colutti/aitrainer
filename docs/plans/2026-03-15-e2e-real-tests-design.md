# E2E Real Tests — Design Document (EXPANDED)

**Data**: 2026-03-15
**Abordagem**: Híbrida — CRUDs reais no backend, Firebase/Stripe/AI mockados
**Meta**: Cobertura E2E máxima (~95%)

---

## Contexto

O projeto tem 20 arquivos E2E mockados em `frontend/e2e/`. Após deep-dive nas 60+ feature components, 60+ shared components e 15 backend endpoints, este documento expande a cobertura para cobrir **todas as features testáveis** do sistema.

## Mapa de Cobertura Completo

### Por Feature (Páginas/Componentes)

| Feature | Componentes | Testes Existentes (mocks) | Testes Reais Planejados | Status |
|---|---|---|---|---|
| **Landing Page** | 13 componentes (Hero, Pricing, FAQ, etc.) | ❌ Nenhum | ✅ Novo | Gap crítico |
| **Login** | LoginPage | ✅ Mockado | ✅ Real | Upgrade |
| **Onboarding** | OnboardingPage, steps | ✅ Mockado | ✅ Real (Firebase mock) | Upgrade |
| **Dashboard** | DashboardPage (769 lines), 7 widgets | ✅ Básico (mock) | ✅ Real + widgets | Expandir |
| **Chat** | ChatPage, MessageBubble | ✅ Mockado | ✅ AI mock, history real | Upgrade |
| **Workouts** | WorkoutsPage | ✅ Mockado | ✅ CRUD real | Upgrade |
| **Body/Weight** | BodyPage, WeightTab, WeightLogDrawer, WeightLogCard | ✅ Mockado | ✅ CRUD real | Upgrade |
| **Body/Nutrition** | NutritionTab, NutritionLogDrawer, MacroCard | ✅ Mockado | ✅ CRUD real | Upgrade |
| **Body/Metabolism** | MetabolismTab | ❌ Nenhum | ✅ Novo | Gap crítico |
| **Memories** | MemoriesPage | ❌ Nenhum | ✅ Novo | Gap crítico |
| **Settings/Profile** | UserProfilePage, PhotoUpload | ✅ Parcial (mock) | ✅ CRUD real | Expandir |
| **Settings/Trainer** | TrainerSettingsPage | ✅ Parcial (mock) | ✅ Real | Upgrade |
| **Settings/Subscription** | SubscriptionPage | ✅ Parcial (mock) | ✅ Real (webhook) | Expandir |
| **Settings/Integrations** | IntegrationsPage (Hevy, Telegram, CSV) | ✅ Parcial (mock) | ✅ Real | Expandir |
| **Navigation** | Sidebar, BottomNav, MainLayout | ✅ Mockado | ✅ Real | Upgrade |
| **UI Components** | QuickAddFAB, IntroTour, ErrorBoundary, Toast, ConfirmationModal | ❌ Parcial | ✅ Em contexto | Expandir |
| **Auth Guards** | ProtectedRoute, AuthGuard | ✅ Mockado | ✅ Real | Upgrade |

### Por Backend Endpoint

| Endpoint | Testes reais planejados |
|---|---|
| `/api/user/login` `/me` `/profile` `/update_profile` `/update_identity` | ✅ Sim |
| `/api/onboarding/complete` `/profile` `/validate` | ✅ Sim |
| `/api/workout/` `/list` `/delete` | ✅ Sim |
| `/api/nutrition/` `/list` `/stats` `/delete` | ✅ Sim |
| `/api/weight/` `/stats` `/delete` | ✅ Sim |
| `/api/dashboard/**` (stats, trends, activities) | ✅ Sim |
| `/api/message/` `/history` | ✅ Sim (AI mock) |
| `/api/trainer/available_trainers` `/update_trainer_profile` | ✅ Sim |
| `/api/memory/` `/delete` | ✅ Sim |
| `/api/metabolism/stats` | ✅ Sim |
| `/api/stripe/create-checkout-session` `/create-portal-session` `/webhook` | ✅ Sim (webhook simulado) |
| `/api/integrations/hevy/**` (status, save, sync, remove) | ✅ Sim |
| `/api/integrations/telegram/**` (status, generate-code, notifications) | ✅ Sim |
| `/api/integrations/imports/**` (mfp, zepp) | ✅ Sim |

---

## Arquitetura

```
frontend/
├── e2e/                        # Testes existentes (UI mockados) — MANTER
├── e2e/real/                   # NOVO — Testes E2E reais
│   ├── fixtures.ts             # Auth helper, cleanup, API client
│   ├── helpers/
│   │   ├── api-client.ts       # Wrapper HTTP para backend
│   │   └── cleanup.ts          # Funções de limpeza
│   ├── auth.setup.ts           # Login real com usuário e2e dedicado
│   ├── 01-landing.spec.ts      # Landing page (público)
│   ├── 02-auth-guards.spec.ts  # Auth guards, redirects, onboarding check
│   ├── 03-onboarding.spec.ts   # Onboarding completo
│   ├── 04-navigation.spec.ts   # Navegação, sidebar, bottom nav
│   ├── 05-dashboard.spec.ts    # Dashboard widgets, charts, payment toast
│   ├── 06-profile.spec.ts      # CRUD perfil + foto
│   ├── 07-workout.spec.ts      # CRUD workouts
│   ├── 08-nutrition.spec.ts    # CRUD nutrition logs + stats
│   ├── 09-weight.spec.ts       # CRUD weight logs + stats
│   ├── 10-metabolism.spec.ts   # TDEE, macros, period selector
│   ├── 11-memories.spec.ts     # CRUD memories + pagination
│   ├── 12-chat.spec.ts         # Chat (AI mock, history real)
│   ├── 13-settings.spec.ts     # Trainer, integrations, preferences
│   ├── 14-integrations.spec.ts # Hevy, Telegram, CSV imports
│   ├── 15-subscription.spec.ts # Planos, webhooks, limites
│   └── 16-ui-components.spec.ts # QuickAddFAB, IntroTour, Toast, ErrorBoundary
└── playwright.config.ts        # projeto "integration"
```

## Pré-requisitos

### 1. Usuário E2E Dedicado
- `e2e-test@fityq.com` no Firebase dev + MongoDB com `onboarding_completed: true`
- Variáveis: `E2E_REAL_USER_EMAIL` e `E2E_REAL_USER_PASSWORD` no `.env`

### 2. Containers Rodando
- `make up` (Backend: `:8000`, Frontend: `:3000`, MongoDB, Qdrant)

---

## Suítes de Teste Detalhadas

### 1. `01-landing.spec.ts` — Landing Page (8 testes) ⭐ NOVO
Testada sem login (página pública).

| # | Teste | O que valida |
|---|---|---|
| 1 | Hero renderiza | Título, subtítulo, CTA visíveis |
| 2 | Navbar links funcionam | Scroll suave para seções (Pricing, FAQ, etc.) |
| 3 | Pricing cards visíveis | 4 planos com preços corretos |
| 4 | FAQ accordion abre/fecha | Click em pergunta expande resposta |
| 5 | Trainer showcase mostra treinadores | Lista de trainers com avatares e descrições |
| 6 | CTA redireciona para registro | Botão "Começar" leva para /login ou /onboarding |
| 7 | Authenticated user redirect | Se logado, `/` redireciona para `/dashboard` |
| 8 | Responsive mobile layout | Hamburger menu, Sticky CTA mobile |

### 2. `02-auth-guards.spec.ts` — Auth Guards (6 testes)

| # | Teste | O que valida |
|---|---|---|
| 1 | Rota protegida sem login → /login | ProtectedRoute redireciona |
| 2 | Login preserva rota original | `state.from` restaurado após login |
| 3 | Onboarding incompleto → /onboarding | `onboarding_completed: false` redireciona |
| 4 | Admin route sem admin → /dashboard | `requireAdmin` bloqueia |
| 5 | Rota inexistente → /dashboard | Catch-all redirect |
| 6 | Logout limpa estado | Após logout, rotas protegidas bloqueiam |

### 3. `03-onboarding.spec.ts` — Onboarding (7 testes)

| # | Teste | O que valida |
|---|---|---|
| 1 | Fluxo completo (Free plan) | Steps: dados pessoais → plano → trainer → conclusão |
| 2 | Validação de campos obrigatórios | Backend rejeita dados inválidos |
| 3 | Idade mínima (18 anos) | Frontend/backend valida |
| 4 | Free plan → apenas GymBro | Outros trainers desabilitados |
| 5 | Preserva dados ao navegar voltar | Campos mantidos entre steps |
| 6 | Seleção de plano visível | Free, Basic, Pro, Premium cards |
| 7 | Perfil salvo no MongoDB | GET `/profile` após onboard retorna dados corretos |

### 4. `04-navigation.spec.ts` — Navegação (6 testes)

| # | Teste | O que valida |
|---|---|---|
| 1 | Sidebar desktop links | Dashboard, Chat, Workouts, Body, Nutrition, Settings |
| 2 | Bottom nav mobile | 5 ícones na barra inferior |
| 3 | Plan badge no sidebar | Badge "Free"/"Basic"/"Pro" correto |
| 4 | Mensagens restantes no sidebar | `X / Y msgs` visível |
| 5 | Logout button funciona | Click → redireciona para login |
| 6 | Active route highlight | Link ativo tem estilo diferente |

### 5. `05-dashboard.spec.ts` — Dashboard (10 testes) ⬆️ EXPANDIDO

| # | Teste | O que valida |
|---|---|---|
| 1 | Saudação com nome do user | "Olá, {nome}!" via `/me` |
| 2 | TDEE/daily target card | Valores reais do `/dashboard/stats` |
| 3 | Consistency score ring | Porcentagem animada no círculo SVG |
| 4 | Macro targets (se disponível) | Proteína, gordura, carboidratos |
| 5 | Weight chart renderiza | LineChart com dados de peso + tendência |
| 6 | Fat/muscle trend (se dados) | Gráficos opcionais visíveis |
| 7 | Recent activities lista | Atividades reais (workouts, weight, nutrition) |
| 8 | Widget Streak | Semanas/dias consecutivos |
| 9 | Widget PRs + Volume + Radar | Componentes de performance |
| 10 | Payment success toast | `?payment=success` mostra notificação |

### 6. `06-profile.spec.ts` — Perfil (6 testes) ⬆️ EXPANDIDO

| # | Teste | O que valida |
|---|---|---|
| 1 | Load profile real | GET `/profile` retorna dados do MongoDB |
| 2 | Update profile (idade, peso, goal) | POST `/update_profile` persiste |
| 3 | Update identity (nome) | POST `/update_identity` persiste |
| 4 | Photo upload | Upload de foto base64 persiste |
| 5 | Validações (idade < 18, peso < 30) | Backend rejeita |
| 6 | Email readonly | Campo desabilitado |

### 7. `07-workout.spec.ts` — Workouts CRUD (6 testes)

| # | Teste |
|---|---|
| 1 | Criar workout |
| 2 | Listar workouts |
| 3 | Ver detalhes (drawer) |
| 4 | Buscar/filtrar |
| 5 | Deletar workout |
| 6 | Estado vazio |

### 8. `08-nutrition.spec.ts` — Nutrição CRUD (7 testes) ⬆️ EXPANDIDO

| # | Teste |
|---|---|
| 1 | Criar registro nutricional |
| 2 | Editar registro |
| 3 | Validação de boundaries |
| 4 | Deletar registro |
| 5 | Stats refletem dados reais |
| 6 | Paginação |
| 7 | MacroCard exibe % correta |

### 9. `09-weight.spec.ts` — Peso CRUD (7 testes) ⬆️ EXPANDIDO

| # | Teste |
|---|---|
| 1 | Criar registro completo (peso + gordura + músculo + medidas) |
| 2 | Editar registro via drawer |
| 3 | Validações (peso < 30, peso > 300) |
| 4 | Deletar registro |
| 5 | Stats refletem dados |
| 6 | Campos opcionais (água, massa óssea) |
| 7 | Trend weight calculado |

### 10. `10-metabolism.spec.ts` — Metabolismo (5 testes) ⭐ NOVO

| # | Teste |
|---|---|
| 1 | TDEE e daily target carregam |
| 2 | Macro targets (proteína, gordura, carbs) |
| 3 | Period selector (2, 4, 8, 12 semanas) |
| 4 | Confidence badge (high/medium/low/none) |
| 5 | Data quality scores (consistency/stability) |

### 11. `11-memories.spec.ts` — Memórias (5 testes) ⭐ NOVO

| # | Teste |
|---|---|
| 1 | Listar memórias da AI |
| 2 | Deletar memória (confirmation dialog) |
| 3 | Paginação (prev/next) |
| 4 | Estado vazio |
| 5 | Total insights counter |

### 12. `12-chat.spec.ts` — Chat (4 testes) ⬆️ EXPANDIDO

| # | Teste |
|---|---|
| 1 | Enviar mensagem (AI mockada) |
| 2 | Histórico persiste entre reloads |
| 3 | Envio via Enter |
| 4 | Empty state (sem histórico) |

### 13. `13-settings.spec.ts` — Settings (5 testes) ⬆️ EXPANDIDO

| # | Teste |
|---|---|
| 1 | Settings page com sub-rotas |
| 2 | Navegar entre abas (Profile, Subscription, Memories, Trainer, Integrations) |
| 3 | Trocar treinador persiste |
| 4 | Listar treinadores disponíveis |
| 5 | Trainer disabled para Free (exceto GymBro) |

### 14. `14-integrations.spec.ts` — Integrações (10 testes) ⭐ EXPANDIDO SIGNIFICATIVAMENTE

| # | Teste |
|---|---|
| 1 | Hevy: salvar API key |
| 2 | Hevy: mostrar status conectado |
| 3 | Hevy: sync workouts |
| 4 | Hevy: remover API key |
| 5 | Telegram: gerar código de link |
| 6 | Telegram: mostrar status linkado |
| 7 | Telegram: toggle notificações |
| 8 | CSV import (MFP/Zepp): upload e resultado |

### 15. `15-subscription.spec.ts` — Assinatura (10 testes) ⬆️ EXPANDIDO

| # | Teste |
|---|---|
| 1 | Usuário Free: badge + página mostram "Free" |
| 2 | 4 plan cards visíveis com preços |
| 3 | Plano atual tem badge "Plano Atual" |
| 4 | Upgrade via webhook (Free → Basic) → badge atualiza |
| 5 | Upgrade via webhook (Basic → Pro) |
| 6 | Downgrade via webhook (Pro → Free) |
| 7 | Limites de mensagem por plano |
| 8 | Reset de counter ao trocar de plano |
| 9 | Botão "Selecionar" chama Stripe checkout |
| 10 | Botão "Gerenciar Cobrança" chama portal (para plano pago) |

### 16. `16-ui-components.spec.ts` — UI Components (7 testes) ⭐ NOVO

| # | Teste |
|---|---|
| 1 | QuickAddFAB: abre e mostra opções (peso, nutrição) |
| 2 | QuickAddFAB: navega para página correta |
| 3 | IntroTour: inicia no primeiro acesso |
| 4 | IntroTour: skip fecha e persiste no localStorage |
| 5 | IntroTour: navega entre steps |
| 6 | Toast: mostra success/error/info |
| 7 | ConfirmationModal: confirma/cancela ação |

---

## Resumo de Cobertura

| Categoria | Testes no Design Inicial | Testes Expandidos | Delta |
|---|---|---|---|
| Landing Page | 0 | 8 | +8 |
| Auth Guards | 0 | 6 | +6 |
| Onboarding | 5 | 7 | +2 |
| Navigation | 0 | 6 | +6 |
| Dashboard | 4 | 10 | +6 |
| Profile | 4 | 6 | +2 |
| Workouts | 6 | 6 | = |
| Nutrition | 6 | 7 | +1 |
| Weight | 6 | 7 | +1 |
| Metabolism | 0 | 5 | +5 |
| Memories | 0 | 5 | +5 |
| Chat | 3 | 4 | +1 |
| Settings | 4 | 5 | +1 |
| Integrations | 0 | 10 | +10 |
| Subscription | 8 | 10 | +2 |
| UI Components | 0 | 7 | +7 |
| **TOTAL** | **46** | **109** | **+63** |

## O que NÃO estamos testando (e por quê)

| Feature | Motivo |
|---|---|
| AI response quality | Mockami a AI — testar qualidade é responsabilidade de testes de integração do LLM |
| Firebase login flow real | Firebase é serviço externo — mockado no Playwright |
| Stripe payment UI real | Stripe Checkout é hosted — não controlamos a UI |
| Admin panel | Requer role admin — pode ser adicionado depois |
| Inactivity logout (50min timer) | Impraticável em E2E — coberto por unit tests |
| i18n completo (pt/en) | Testamos apenas idioma padrão — variações são unit test |

## Estratégia de Limpeza de Dados

```
beforeAll → login, obter JWT
beforeEach → (nada)
afterAll → limpar TODOS dados do e2e user
```

Cleanup via API direta:
1. `GET /api/workout/list` → `DELETE` cada
2. `GET /api/nutrition/list` → `DELETE` cada
3. `GET /api/weight` → `DELETE` cada
4. `GET /api/memory` → `DELETE` cada
5. `POST /api/user/update_profile` → restaurar defaults
6. Webhook `subscription.deleted` → resetar para Free

## Como Rodar

```bash
make up
cd frontend && npx playwright test --project=integration    # Reais
cd frontend && npx playwright test --project=chromium       # Mockados (existentes)
```
