# Migração Frontend: Angular 21 → React 19 + Vite

## Contexto

O frontend Angular atual tem problemas acumulados de produtividade:
- **Testes Cypress frágeis**: 30 arquivos E2E com falhas frequentes (overflow visibility, timeouts, mocks duplicados em 60+ intercepts)
- **Boilerplate**: imports longos (16+ por componente), configs Chart.js repetitivas (~500 linhas), pagination duplicada
- **Ciclo lento**: mudanças simples quebram testes não relacionados, retrabalho constante
- **Acoplamento**: testes dependem de DOM structure, CSS visibility, timing de requests async

**Decisão**: Reescrever o frontend completo em React 19 + Vite (SPA) com feature folders isolados, usando TDD.

**Estratégia de migração**: Criar em branch separada (`feat/react-migration`). Quando pronto, deletar `frontend/` e renomear `frontend-react/` para `frontend/`. Corte limpo — sem coexistência.

---

## Princípios Obrigatórios

1. **TDD (Test-Driven Development)**: Para cada módulo, escrever testes ANTES da implementação. Ciclo: Red → Green → Refactor. Nenhum código de produção sem teste correspondente.
2. **Alta cobertura de testes**: Meta ≥90% de cobertura em stores, hooks, API functions e utils. Componentes testados via Testing Library (comportamento, não implementação). Zero dependência de E2E para validar lógica.
3. **Arquitetura escalável**: Feature folders com fronteiras rígidas. Shared components genéricos e reutilizáveis. Custom hooks encapsulam lógica de negócio. Adicionar nova feature = criar nova pasta, sem tocar em código existente.
4. **Código documentado**: JSDoc em todas as funções públicas, hooks e stores. README por feature explicando propósito e uso. Tipos TypeScript explícitos (sem `any`, sem `as` desnecessário).
5. **Zero warnings**: ESLint flat config + Prettier strict. TypeScript strict mode (`strict: true`, `noUncheckedIndexedAccess: true`). Zero warnings no build e no lint. CI falha em qualquer warning.
6. **Versões mais recentes**: React 19, Vite 6, TypeScript 5.7+, TailwindCSS v4, Zustand 5, Recharts 2.15+, Vitest 3, Playwright 1.50+, React Router 7, react-hook-form 7 + Zod. Lock de versões via `package-lock.json`.
7. **UI moderna e concisa**: shadcn/ui como base, design system consistente. Componentes pequenos e focados. Mobile-first responsive. Dark theme nativo (existente no Tailwind theme).

---

## Stack Alvo

| Atual (Angular) | Novo (React) |
|------------------|--------------|
| Angular 21 | React 19 + Vite 6 |
| Angular Signals | Zustand 5 |
| HttpClient + firstValueFrom | fetch wrapper nativo |
| Chart.js + ng2-charts | Recharts 2.15+ |
| Jest + Cypress | Vitest 3 + Testing Library + Playwright 1.50+ |
| NavigationService (signals) | React Router 7 (URLs reais) |
| Angular Reactive Forms | react-hook-form 7 + Zod |
| lucide-angular | lucide-react |
| ngx-markdown | react-markdown |
| TailwindCSS v4 | TailwindCSS v4 (mesmo) |
| — | shadcn/ui (novo) |

**O que NÃO muda**: Backend (FastAPI), JWT em localStorage, API contracts, assets estáticos, paleta de cores.

**O que muda além do código**: `podman-compose.yml` (aponta pro novo frontend), `Makefile` (novos comandos), `CLAUDE.md` (atualizar stack), `Dockerfile` (Vite build), `nginx.conf` (mínimas mudanças).

---

## Estrutura de Pastas

```
frontend/                         ← (após rename de frontend-react/)
  public/
    assets/                       ← copiados do Angular (avatares de trainers)
  src/
    main.tsx                      ← entry point
    App.tsx                       ← router setup + auth guard
    index.css                     ← copiado do Angular (tema Tailwind @theme)
    shared/
      api/
        http-client.ts            ← fetch wrapper com auth + error handling
        http-client.test.ts       ← testes colocados
      components/
        ui/                       ← shadcn/ui components
        Toast.tsx
        Toast.test.tsx
        Skeleton.tsx
        ConfirmationModal.tsx
        ConfirmationModal.test.tsx
        DateInput.tsx
        DateInput.test.tsx
        NumberInput.tsx
        NumberInput.test.tsx
      hooks/
        useAuth.ts                ← Zustand store
        useAuth.test.ts
        useNotification.ts        ← Zustand store
        useNotification.test.ts
        useConfirmation.ts
        useConfirmation.test.ts
        useTokenExpiration.ts
        useTokenExpiration.test.ts
        usePagination.ts
        usePagination.test.ts
      types/                      ← copiados do Angular (interfaces puras)
        message.ts
        nutrition.ts
        workout.ts
        weight-log.ts
        metabolism.ts
        user-profile.ts
        trainer-profile.ts
        stats.ts
        integration.ts
        import-result.ts
        memory.ts
      utils/
        format-date.ts            ← substitui AppDateFormatPipe
        format-date.test.ts
        format-number.ts          ← substitui AppNumberFormatPipe
        format-number.test.ts
    features/
      auth/
        components/
          LoginPage.tsx
          LoginPage.test.tsx
        api/
          auth-api.ts
          auth-api.test.ts
        index.ts
      chat/
        components/
          ChatPage.tsx
          ChatPage.test.tsx
          MessageBubble.tsx
          MessageBubble.test.tsx
        hooks/
          useChat.ts
          useChat.test.ts
        api/
          chat-api.ts
          chat-api.test.ts
        index.ts
      dashboard/
        components/
          DashboardPage.tsx
          DashboardPage.test.tsx
        widgets/
          ChartCard.tsx            ← wrapper genérico (título, loading, empty)
          ChartCard.test.tsx
          CustomTooltip.tsx        ← tooltip dark theme reutilizável
          WidgetStreak.tsx
          WidgetFrequency.tsx
          WidgetMacrosToday.tsx    ← PieChart
          WidgetLineChart.tsx      ← genérico
          WidgetBarChart.tsx       ← genérico
          WidgetRadar.tsx          ← RadarChart
          ... (cada widget com .test.tsx colocado)
        api/
          dashboard-api.ts
          dashboard-api.test.ts
        index.ts
      body/
        components/
          BodyPage.tsx
          BodyPage.test.tsx
          WeightTab.tsx
          WeightTab.test.tsx
          NutritionTab.tsx
          NutritionTab.test.tsx
          MetabolismTab.tsx
          MetabolismTab.test.tsx
        widgets/
          WidgetWeightHistogram.tsx
          WidgetCalorieHistory.tsx
          WidgetAverageCalories.tsx
          ... (cada com .test.tsx)
        hooks/
          useWeightTab.ts
          useWeightTab.test.ts
          useNutritionTab.ts
          useNutritionTab.test.ts
          useMetabolismTab.ts
          useMetabolismTab.test.ts
        api/
          body-api.ts
          body-api.test.ts
        index.ts
      workouts/
        components/
          WorkoutsPage.tsx
          WorkoutsPage.test.tsx
          WorkoutDrawer.tsx
          WorkoutDrawer.test.tsx
        api/
          workouts-api.ts
          workouts-api.test.ts
        index.ts
      nutrition/
        components/
          NutritionPage.tsx
          NutritionPage.test.tsx
        api/
          nutrition-api.ts
          nutrition-api.test.ts
        index.ts
      memories/
        components/
          MemoriesPage.tsx
          MemoriesPage.test.tsx
        api/
          memories-api.ts
          memories-api.test.ts
        index.ts
      settings/
        components/
          UserProfilePage.tsx
          UserProfilePage.test.tsx
          TrainerSettingsPage.tsx
          TrainerSettingsPage.test.tsx
          IntegrationsPage.tsx
          IntegrationsPage.test.tsx
        api/
          settings-api.ts
          settings-api.test.ts
        index.ts
      admin/
        components/
          AdminDashboardPage.tsx
          AdminUsersPage.tsx
          AdminLogsPage.tsx
          AdminPromptsPage.tsx
          ... (cada com .test.tsx)
        api/
          admin-api.ts
          admin-api.test.ts
        index.ts
      onboarding/
        components/
          OnboardingPage.tsx
          OnboardingPage.test.tsx
        api/
          onboarding-api.ts
          onboarding-api.test.ts
        index.ts
  Dockerfile
  nginx.conf
  vite.config.ts
  vitest.config.ts
  tsconfig.json
  package.json
  .eslintrc.js                    ← ESLint flat config
  .prettierrc
  playwright.config.ts
  e2e/                            ← testes Playwright E2E
    login.spec.ts
    chat.spec.ts
    dashboard.spec.ts
    nutrition-crud.spec.ts
    workout-crud.spec.ts
    weight-crud.spec.ts
    navigation.spec.ts
    onboarding.spec.ts
  README.md
```

**Regras de isolamento**:
- Features NUNCA importam de outras features
- Features só importam de `shared/`
- `vitest run src/features/nutrition` roda testes só de nutrition
- Cada feature exporta via `index.ts` barrel (só componentes de página)

**Regras de código**:
- Toda função pública tem JSDoc
- Todo hook customizado tem JSDoc com `@example`
- Todo componente exportado tem `/** @description */`
- TypeScript `strict: true` + `noUncheckedIndexedAccess: true`
- ESLint flat config + `@typescript-eslint/strict` + `eslint-plugin-react`
- Prettier com config padrão
- Testes colocados: `useAuth.test.ts` ao lado de `useAuth.ts`
- `npm run lint` e `npm run typecheck` passam com zero warnings
- Imports organizados automaticamente via eslint-plugin-import

---

## Fases de Migração

### Fase 0: Scaffolding + Qualidade

**O que fazer:**
- Criar branch `feat/react-migration`
- Criar projeto React 19 + Vite 6 + TypeScript 5.7 strict em `frontend-react/`
- Configurar TailwindCSS v4 (copiar `index.css` com tema `@theme` do Angular)
- Configurar env vars: `VITE_API_URL` (dev: `/api`, prod: URL Render via build arg)
- Instalar dependências:
  - Core: `react`, `react-dom`, `react-router`
  - State: `zustand`
  - Forms: `react-hook-form`, `zod`, `@hookform/resolvers`
  - Charts: `recharts`
  - UI: `shadcn/ui` (via CLI), `lucide-react`
  - Markdown: `react-markdown`, `remark-gfm`, `rehype-highlight`
  - Auth: `jwt-decode`
  - Dev: `typescript`, `vite`, `@vitejs/plugin-react`
  - Test: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, `msw` (mock service worker)
  - Lint: `eslint`, `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-import`, `prettier`
  - E2E: `@playwright/test`
- Copiar 12 arquivos de models/types (interfaces puras, zero dependência Angular)
- Copiar assets (avatares de trainers) para `public/assets/`
- Configurar `vite.config.ts` com proxy dev (`/api` → `localhost:8000`)
- Configurar `tsconfig.json` com `strict: true`, `noUncheckedIndexedAccess: true`, path aliases (`@shared/`, `@features/`)
- Configurar `vitest.config.ts` com jsdom, coverage istanbul, thresholds `{ branches: 90, functions: 90, lines: 90, statements: 90 }`
- Configurar ESLint flat config
- Configurar Prettier
- Configurar scripts npm:
  - `dev` — Vite dev server (porta 3000)
  - `build` — Vite production build
  - `preview` — preview do build
  - `test` — Vitest
  - `test:watch` — Vitest watch mode
  - `test:coverage` — Vitest com coverage
  - `test:e2e` — Playwright
  - `lint` — ESLint
  - `lint:fix` — ESLint fix
  - `typecheck` — `tsc --noEmit`
  - `check` — lint + typecheck + test (pré-commit)
- Configurar `playwright.config.ts`

**Validação:**
- `npm run dev` abre shell vazio com tema Tailwind correto (dark theme)
- `npm run lint` passa com zero warnings
- `npm run typecheck` passa com zero errors
- `npm test` roda (0 testes, 0 falhas)
- `npm run test:coverage` mostra thresholds configurados

**Arquivos Angular fonte para referência:**
- `frontend/index.css` (tema Tailwind)
- `frontend/src/models/*.ts` (interfaces TypeScript)
- `frontend/src/assets/` (avatares)

---

### Fase 1: Core (Auth + Navegação + Notificações + Layout)

**Fluxo TDD por módulo:**

1. **`http-client.ts`** — Testes primeiro:
   - Teste: auto-attach Bearer token quando existe no localStorage
   - Teste: request sem token quando não autenticado
   - Teste: 401 → chama logout, redireciona para /login
   - Teste: 429 → mostra toast "Muitas requisições"
   - Teste: 5xx → mostra toast "Erro no servidor"
   - Teste: network error (status 0) → mostra toast "Erro de conexão"
   - Teste: throttle de notificações de sessão expirada (5s debounce)
   - Implementar fetch wrapper

2. **`useAuth` store** — Testes primeiro:
   - Teste: login com credenciais válidas → salva token, isAuthenticated=true
   - Teste: login com credenciais inválidas → erro, isAuthenticated=false
   - Teste: logout → limpa token, isAuthenticated=false, redireciona /login
   - Teste: loadUserInfo → popula userInfo e isAdmin
   - Teste: getToken → retorna token do localStorage
   - Teste: init → verifica token existente, chama loadUserInfo
   - Implementar Zustand store

3. **`useNotification` store** — Testes primeiro:
   - Teste: show() adiciona toast com id único
   - Teste: success/error/info helpers
   - Teste: remove() remove toast por id
   - Teste: toast auto-remove após duration
   - Implementar store

4. **`useConfirmation` store** — Testes primeiro:
   - Teste: confirm(message) retorna Promise que resolve true no accept
   - Teste: confirm(message) retorna Promise que resolve false no cancel
   - Implementar store

5. **`useTokenExpiration` hook** — Testes primeiro:
   - Teste: detecta JWT expirado, chama logout
   - Teste: cleanup do timer no unmount
   - Implementar hook com useEffect + setTimeout

6. **`format-date.ts` e `format-number.ts`** — Testes primeiro:
   - Teste: cada formato (8 presets de data, 5 de número) com valores conhecidos em pt-BR
   - Teste: edge cases (null, undefined, NaN, string inválida)
   - Implementar com Intl.DateTimeFormat/NumberFormat pt-BR

7. **React Router setup** — Testes primeiro:
   - Teste: rota `/` redireciona para `/dashboard` se autenticado
   - Teste: rota `/` mostra login se não autenticado
   - Teste: rota `/dashboard`, `/workouts`, `/chat`, `/body`, etc.
   - Teste: rota protegida redireciona para `/login` se não autenticado
   - Implementar router com lazy loading (React.lazy + Suspense)

8. **Layout components** — Testes com Testing Library:
   - `Sidebar.tsx`: render, click navega (React Router link), item ativo highlighted
   - `BottomNav.tsx`: render, click navega, responsivo (mobile only)
   - `AppLayout.tsx`: render com sidebar + content area + bottom nav
   - `Toast.tsx`: render com mensagem, auto-dismiss
   - `ConfirmationModal.tsx`: render, confirmar retorna true, cancelar retorna false
   - `Skeleton.tsx`: render com variantes (text, card, chart)

9. **`LoginPage.tsx`** — Testes com Testing Library:
   - Teste: render form com email + senha
   - Teste: validação com react-hook-form + Zod (email obrigatório, senha obrigatória)
   - Teste: submit chama auth-api.login
   - Teste: erro mostra mensagem
   - Teste: sucesso redireciona para /dashboard
   - Implementar com react-hook-form + Zod + shadcn/ui

**Arquivos Angular fonte:**
- `frontend/src/services/auth.service.ts`
- `frontend/src/services/navigation.service.ts`
- `frontend/src/services/notification.service.ts`
- `frontend/src/services/confirmation.service.ts`
- `frontend/src/services/token-expiration.service.ts`
- `frontend/src/services/jwt.interceptor.ts`
- `frontend/src/services/error.interceptor.ts`
- `frontend/src/app.component.ts` + `frontend/src/app.component.html`
- `frontend/src/components/login/`
- `frontend/src/components/sidebar/`
- `frontend/src/components/bottom-nav/`
- `frontend/src/pipes/date-format.pipe.ts`
- `frontend/src/pipes/number-format.pipe.ts`

**Validação:**
- `npm test` — todos testes passam
- `npm run test:coverage` — ≥90% nos stores, hooks, utils e API
- `npm run lint` — zero warnings
- Login funciona manualmente com backend real
- Sidebar navega entre rotas (URL muda)
- Toasts aparecem
- Auto-logout no token expirado redireciona para /login

---

### Fase 2: Chat (Streaming)

**Fluxo TDD:**

1. **`chat-api.ts`** — Testes primeiro:
   - Teste: loadHistory retorna mensagens ordenadas
   - Teste: clearHistory faz DELETE e retorna sucesso
   - Teste: sendMessage abre stream, acumula chunks, retorna texto completo
   - Mock de ReadableStream para testar streaming
   - Implementar API functions (streaming usa fetch nativo, não http-client)

2. **`useChat` store** — Testes primeiro:
   - Teste: messages inicia vazio
   - Teste: loadHistory popula messages
   - Teste: sendMessage adiciona user message + ai placeholder
   - Teste: durante streaming, isTyping=true e ai message atualiza progressivamente
   - Teste: após streaming, isTyping=false
   - Teste: clearHistory reseta messages
   - Implementar Zustand store

3. **`MessageBubble.tsx`** — Testes primeiro:
   - Teste: render user message com estilo correto
   - Teste: render ai message com markdown renderizado
   - Teste: code blocks renderizam com syntax highlight
   - Implementar com react-markdown + remark-gfm + rehype-highlight

4. **`ChatPage.tsx`** — Testes com Testing Library:
   - Teste: render mostra histórico de mensagens
   - Teste: submit envia mensagem e mostra na lista
   - Teste: textarea auto-resize ao digitar
   - Teste: scroll automático para última mensagem
   - Teste: Enter envia, Shift+Enter quebra linha
   - Implementar componente

**Arquivo Angular fonte:** `frontend/src/services/chat.service.ts`

**Validação:**
- `npm test src/features/chat` — todos passam com ≥90% coverage
- Chat streaming funciona com backend real
- Markdown (headers, listas, code blocks) renderiza corretamente

---

### Fase 3: Dashboard + Widgets

**Fluxo TDD:**

1. **`dashboard-api.ts`** — Testes primeiro:
   - Teste: fetchWorkoutStats retorna WorkoutStats tipado
   - Teste: fetchNutritionStats retorna NutritionStats tipado
   - Teste: fetchMetabolismSummary retorna MetabolismSummary tipado
   - Teste: fetchBodyCompositionStats retorna BodyCompositionStats tipado
   - Teste: fetchTrainerProfile retorna TrainerProfile tipado
   - Implementar API functions

2. **Shared chart components** — Testes primeiro:
   - `ChartCard.tsx`: wrapper genérico com título, loading skeleton, empty state, error state
   - `CustomTooltip.tsx`: tooltip dark theme reutilizável (`bg-zinc-900`, `border-zinc-700`)
   - Cada widget com 3 testes mínimos: render com dados, empty state, loading state

3. **Widgets individuais** (cada com testes TDD):
   - `WidgetStreak` — stat card (sem chart)
   - `WidgetFrequency` — calendar dots (sem chart)
   - `WidgetRecentPrs` — tabela/lista
   - `WidgetMacrosToday` — PieChart (doughnut) com Recharts
   - `WidgetAdherence` — indicadores visuais
   - `WidgetMetabolicGauge` — SVG gauge customizado
   - `WidgetBodyEvolution` — stat cards
   - `WidgetLineChart` — wrapper genérico para LineChart Recharts
   - `WidgetMacroTargets` — progress bars
   - `WidgetTdeeSummary` — stat card
   - `WidgetLastActivity` — stat card
   - `WidgetWeeklyDistribution` — BarChart Recharts
   - `WidgetStrengthRadar` — RadarChart Recharts
   - `SectionHeader` — header com ícone

4. **`DashboardPage.tsx`** — Testes de integração:
   - Teste: render com dados mock mostra todos widgets
   - Teste: loading state mostra skeletons em cada widget
   - Teste: erro na API mostra estado de erro

**Tradução Chart.js → Recharts:**
- `ChartConfiguration` objeto imperativo → JSX declarativo (`<LineChart>`, `<BarChart>`, `<PieChart>`)
- `backgroundColor`/`borderColor` → prop `fill`/`stroke`
- `scales.x/y` → componentes `<XAxis>`, `<YAxis>`
- `responsive: true` → `<ResponsiveContainer width="100%" height={...}>`
- Palette de cores mantida: `#10b981` (verde), `#3b82f6` (azul), `#f97316` (laranja), `#facc15` (amarelo)
- Tooltip bg: `#18181b`, border: `#3f3f46`, text: `#fafafa`
- Axis text: `#a1a1aa`, grid: `#27272a`

**Validação:**
- `npm test src/features/dashboard` — todos passam com ≥90% coverage
- `npm run lint` — zero warnings
- Dashboard renderiza visualmente correto com backend real

---

### Fase 4: Body (Peso + Nutrição + Metabolismo tabs)

**Fluxo TDD:**

1. **`body-api.ts`** — Testes primeiro:
   - Weight: logWeight, getHistory, getBodyCompositionStats, deleteWeight, importZeppLife
   - Nutrition: getNutritionLogs, getNutritionStats, logNutrition, deleteNutrition
   - Metabolism: getMetabolismSummary, getMetabolismDefault
   - Implementar API functions

2. **Hooks de tab** — Testes primeiro:
   - `useWeightTab`: estado do form (react-hook-form), submit, validação Zod, paginação, loading
   - `useNutritionTab`: estado do form, submit, validação, paginação, filtro por dias
   - `useMetabolismTab`: carregamento de dados, computed values (TDEE, déficit, etc.)

3. **Shared input components** (se não existirem da Fase 1) — Testes primeiro:
   - `DateInput.tsx`: render, seleção de data via datepicker, formato pt-BR dd/MM/yyyy, validação
   - `NumberInput.tsx`: render, aceita `.` e `,` como decimal, rejeita letras, validação numérica

4. **Widgets específicos de Body** — Testes primeiro:
   - `WidgetWeightHistogram`, `WidgetCalorieHistory`, `WidgetCalorieVolatility`
   - `WidgetAverageCalories`, `WidgetDataQuality`, `WidgetCaloriesWeightComparison`
   - (Reutiliza widgets genéricos da Fase 3: WidgetLineChart, WidgetMacrosToday, etc.)

5. **Sub-componentes de página** — Testes de integração:
   - `WeightTab.tsx`: form de entrada + histórico + charts
   - `NutritionTab.tsx`: form de entrada + lista + charts
   - `MetabolismTab.tsx`: dados calculados + charts
   - `BodyPage.tsx`: troca de tabs funciona, cada tab carrega seus dados

**Arquivos Angular fonte:**
- `frontend/src/components/body/body.component.ts` (496 linhas, 29 signals → quebrar em 3 hooks + 3 tabs)
- `frontend/src/services/weight.service.ts`
- `frontend/src/services/nutrition.service.ts`
- `frontend/src/services/metabolism.service.ts`

**Validação:**
- `npm test src/features/body` — todos passam com ≥90% coverage
- 3 tabs funcionam manualmente: forms, delete com confirmação, paginação, charts

---

### Fase 5: Workouts + Nutrition (páginas standalone)

**Fluxo TDD:**

1. **`workouts-api.ts`** e **`nutrition-api.ts`** — Testes primeiro

2. **`usePagination` hook** (shared) — Testes primeiro:
   - Teste: nextPage incrementa page
   - Teste: prevPage decrementa (mínimo 1)
   - Teste: reset volta para page 1
   - Teste: totalPages computation baseada em total + pageSize

3. **`WorkoutsPage.tsx` + `WorkoutDrawer.tsx`** — Testes primeiro:
   - Teste: lista paginada renderiza workouts
   - Teste: click em workout abre drawer com exercícios detalhados
   - Teste: paginação funciona (next/prev)

4. **`NutritionPage.tsx`** — Testes primeiro:
   - Teste: lista paginada com filtro por dias (7, 30, 90)
   - Teste: delete com modal de confirmação
   - Teste: widgets de stats renderizam

**Arquivos Angular fonte:**
- `frontend/src/components/workouts/workouts.component.ts`
- `frontend/src/components/nutrition/nutrition.component.ts`

**Validação:**
- `npm test src/features/workouts src/features/nutrition` — todos passam ≥90% coverage

---

### Fase 6: Settings + Integrações + Memories

**Fluxo TDD:**

1. **`settings-api.ts`** e **`memories-api.ts`** — Testes primeiro

2. **Componentes** — Testes primeiro para cada:
   - `UserProfilePage.tsx`: form com react-hook-form + Zod (nome, idade, peso, altura, gênero, goal)
   - `TrainerSettingsPage.tsx`: grid de cards com avatares, seleção salva via API
   - `IntegrationsPage.tsx`: seções isoladas para cada integração
     - Hevy: input API key, validar, importar, webhook management
     - MFP: upload CSV, progress
     - Zepp Life: upload CSV, progress
     - Telegram: gerar código, verificar link, preferências de notificação
   - `MemoriesPage.tsx`: lista paginada, search, delete com confirmação

**Arquivos Angular fonte:**
- `frontend/src/components/user-profile/`
- `frontend/src/components/trainer-settings/`
- `frontend/src/components/integrations/`
- `frontend/src/components/memories/`
- `frontend/src/services/hevy.service.ts`
- `frontend/src/services/import.service.ts`
- `frontend/src/services/telegram.service.ts`
- `frontend/src/services/memory.service.ts`

**Validação:**
- `npm test src/features/settings src/features/memories` — todos passam ≥90% coverage

---

### Fase 7: Admin

**Fluxo TDD:**

1. **`admin-api.ts`** — Testes primeiro

2. **Guard de acesso** — Testes primeiro:
   - Teste: rota `/admin/*` redireciona para `/dashboard` se `isAdmin=false`
   - Teste: rota `/admin/*` renderiza se `isAdmin=true`

3. **Componentes** — Testes primeiro:
   - `AdminDashboardPage.tsx`: analytics overview
   - `AdminUsersPage.tsx`: lista users, detalhes, update, delete
   - `AdminLogsPage.tsx`: visualizador de logs com filtros
   - `AdminPromptsPage.tsx`: histórico de prompts

**Arquivo Angular fonte:** `frontend/src/components/admin/`

**Validação:**
- `npm test src/features/admin` — todos passam ≥90% coverage

---

### Fase 8: Onboarding

**Fluxo TDD:**

1. **`onboarding-api.ts`** — Testes primeiro

2. **`OnboardingPage.tsx`** — Testes primeiro:
   - Teste: step 1 — input de token, validação via API
   - Teste: step 2 — form de senha com confirmação, validação Zod
   - Teste: step 3 — form de perfil (nome, idade, peso, altura, gênero)
   - Teste: step 4 — seleção de trainer (grid com avatares)
   - Teste: navegação entre steps (next/back)
   - Teste: submit final cria conta e redireciona para /dashboard

**Arquivo Angular fonte:** `frontend/src/components/onboarding/`

**Validação:**
- `npm test src/features/onboarding` — todos passam ≥90% coverage

---

### Fase 9: E2E + Docker + Deploy + Documentação + Cleanup

**Testes E2E com Playwright:**
- ~10-15 testes focados em fluxos críticos end-to-end
- Mocks via Playwright `page.route()` (intercepta no nível de rede)
- Testes:
  1. `login.spec.ts` — login com credenciais válidas/inválidas
  2. `chat.spec.ts` — enviar mensagem, ver resposta streaming
  3. `dashboard.spec.ts` — dashboard carrega com widgets
  4. `nutrition-crud.spec.ts` — criar, listar, deletar nutrition log
  5. `weight-crud.spec.ts` — registrar peso, ver histórico, deletar
  6. `workout-crud.spec.ts` — listar workouts, abrir detalhes
  7. `navigation.spec.ts` — navegar entre todas rotas, back button funciona
  8. `onboarding.spec.ts` — fluxo completo de onboarding

**Docker:**
```dockerfile
FROM node:22-slim AS build
ARG VITE_API_URL=https://aitrainer-backend.onrender.com
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ENV VITE_API_URL=$VITE_API_URL
RUN npm run lint && npm run typecheck
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**nginx.conf** (atualizar do Angular):
- SPA routing: `try_files $uri $uri/ /index.html;` (mesmo)
- Static cache: hashed assets 1 year (Vite usa content hashes também)
- HTML no-cache (mesmo)
- API proxy: `/api/` → `http://backend:8000/` (mesmo)
- Streaming support: `proxy_buffering off` (mesmo)
- Gzip: habilitado level 6 (mesmo)

**Atualizações de infraestrutura:**
- `podman-compose.yml`: atualizar path do build do frontend
- `Makefile`: atualizar comandos frontend (npm run dev, npm test, etc.)
- `CLAUDE.md`: atualizar seções de stack, comandos, arquitetura frontend

**Documentação:**
- `README.md` principal: setup, comandos, arquitetura, como adicionar nova feature
- JSDoc em 100% das funções, hooks e stores públicas (já feito durante TDD)
- Cada feature tem barrel export (`index.ts`) documentado

**Cleanup final:**
- Deletar `frontend/` (Angular antigo)
- Renomear `frontend-react/` → `frontend/`
- Atualizar todas referências em docker-compose, Makefile, CLAUDE.md
- Verificar que CI/CD (GitHub Actions) funciona com novos comandos

**Validação final:**
- `npm run lint` — zero warnings, zero errors
- `npm run typecheck` — zero errors, strict mode
- `npm test` — todos testes unitários passam
- `npm run test:coverage` — ≥90% branches, functions, lines, statements
- `npm run test:e2e` — todos Playwright E2E passam
- `npm run build` — build de produção sem warnings
- `docker build .` — build Docker funciona (inclui lint + typecheck)
- Deploy no Render — app funciona em produção
- Testar manualmente: login, chat streaming, dashboard, body (3 tabs), workouts, nutrition, memories, settings, integrações, admin, onboarding
- Zero `any`, zero `as` desnecessário, zero `// @ts-ignore`, zero `eslint-disable`

---

## Dependências Entre Fases

```
Fase 0 (Scaffolding)
  │
  ▼
Fase 1 (Core: auth, router, layout, notificações)
  │
  ├──▶ Fase 2 (Chat)
  │
  ├──▶ Fase 3 (Dashboard + Widgets) ──▶ Fase 4 (Body) ──▶ Fase 5 (Workouts + Nutrition)
  │
  ├──▶ Fase 6 (Settings + Integrações + Memories)
  │
  ├──▶ Fase 7 (Admin)
  │
  ├──▶ Fase 8 (Onboarding)
  │
  ▼
Fase 9 (E2E + Docker + Deploy + Cleanup)
```

Ordem recomendada: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9.
Fases 3/4 antes de 5 porque estabelecem padrões de chart reutilizados.

---

## Padrões de Tradução

| Angular | React |
|---------|-------|
| `signal<T>(initial)` | Zustand state field |
| `computed(() => ...)` | `useMemo` ou Zustand derived selector |
| `effect(() => { ... })` | `useEffect` com dependency array |
| `signal.set(value)` | Zustand action: `set({ field: value })` |
| `signal.update(fn)` | Zustand action: `set(state => ({ field: fn(state.field) }))` |
| `inject(Service)` | `useStore()` hook ou import direto de API function |
| `{{ value \| appDateFormat:'medium' }}` | `{formatDate(value, 'medium')}` |
| `@if (condition)` | `{condition && <Component />}` |
| `@for (item of items; track item.id)` | `{items.map(item => <Component key={item.id} />)}` |
| `@switch (view)` | React Router `<Routes>` com `<Route>` |
| `firstValueFrom(this.http.get(...))` | `await httpClient('/endpoint')` |
| `NavigationService.navigateTo('view')` | `useNavigate()('/path')` |
| Angular Reactive Forms | `useForm()` de react-hook-form + Zod schema |
| `@Input() prop` | Props do componente React |
| `@Output() event` | Callback props (`onDelete`, `onChange`) |
| `ngOnInit` | `useEffect(() => {...}, [])` |
| `ngOnDestroy` | `useEffect` cleanup function |
| `@defer` | `React.lazy()` + `<Suspense>` |

---

## Rotas (React Router)

| Rota | Componente | Auth | Admin |
|------|-----------|------|-------|
| `/login` | LoginPage | Não | Não |
| `/onboarding` | OnboardingPage | Não | Não |
| `/` | redirect → `/dashboard` | Sim | Não |
| `/dashboard` | DashboardPage | Sim | Não |
| `/chat` | ChatPage | Sim | Não |
| `/body` | BodyPage | Sim | Não |
| `/workouts` | WorkoutsPage | Sim | Não |
| `/nutrition` | NutritionPage | Sim | Não |
| `/memories` | MemoriesPage | Sim | Não |
| `/settings/profile` | UserProfilePage | Sim | Não |
| `/settings/trainer` | TrainerSettingsPage | Sim | Não |
| `/settings/integrations` | IntegrationsPage | Sim | Não |
| `/admin` | AdminDashboardPage | Sim | Sim |
| `/admin/users` | AdminUsersPage | Sim | Sim |
| `/admin/logs` | AdminLogsPage | Sim | Sim |
| `/admin/prompts` | AdminPromptsPage | Sim | Sim |

---

## Verificação Final Completa

Após migração completa:
1. `npm run lint` — zero warnings, zero errors
2. `npm run typecheck` — zero errors, strict mode
3. `npm test` — todos testes unitários passam
4. `npm run test:coverage` — ≥90% branches, functions, lines, statements
5. `npm run test:e2e` — todos Playwright E2E passam
6. `npm run build` — build de produção sem warnings
7. `docker build .` — build Docker funciona (inclui lint + typecheck)
8. `make up` — podman-compose sobe frontend + backend + mongo + qdrant
9. Deploy no Render — app funciona em produção
10. Testar manualmente todas features
11. Zero `any`, zero `as` desnecessário, zero `// @ts-ignore`, zero `eslint-disable`
12. JSDoc em todas funções públicas
13. README.md principal e barrel exports documentados
14. CLAUDE.md atualizado com nova stack
