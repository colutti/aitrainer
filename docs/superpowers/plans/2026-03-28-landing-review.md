# Landing Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corrigir a landing page para remover chaves sem tradução, restaurar CTAs e descrições dos planos, refletir integrações reais e alinhar toda a copy crítica com o estado atual do produto.

**Architecture:** A implementação vai alinhar o contrato entre os componentes de landing e os arquivos de locale, preenchendo chaves ausentes e ajustando componentes que hoje assumem formatos incorretos. A execução seguirá TDD nos pontos com regressão visível, depois consolidará a revisão editorial e validará frontend com testes, lint e typecheck.

**Tech Stack:** React 19, TypeScript, Vitest, React Testing Library, react-i18next

---

## File Map

- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.tsx`
- Modify: `frontend/src/features/landing/components/HowItWorks.tsx`
- Modify: `frontend/src/features/landing/components/TrainerShowcase.tsx`
- Modify: `frontend/src/features/landing/components/ChatCarousel.tsx`
- Modify: `frontend/src/features/landing/components/ProductShowcase.tsx`
- Modify: `frontend/src/features/landing/components/Footer.tsx`
- Modify: `frontend/src/features/landing/components/Pricing.test.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.test.tsx`
- Modify: `frontend/src/features/landing/components/HowItWorks.test.tsx`
- Modify: `frontend/src/features/landing/components/ProductShowcase.test.tsx`
- Modify: `frontend/src/features/landing/components/Footer.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`

### Task 1: Lock The Pricing And Integration Regressions With Failing Tests

**Files:**
- Modify: `frontend/src/features/landing/components/Pricing.test.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.test.tsx`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`
- Test: `frontend/src/features/landing/components/IntegrationLogos.test.tsx`

- [ ] **Step 1: Write the failing tests**

```tsx
it('renders a translated CTA for each pricing plan', () => {
  render(<Pricing />);

  expect(screen.getByRole('button', { name: /comecar gratis/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /assinar basic/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /assinar pro/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /assinar premium/i })).toBeInTheDocument();
});

it('shows integrations as available instead of coming soon', () => {
  render(<IntegrationLogos />);

  expect(screen.queryByText(/em breve/i)).not.toBeInTheDocument();
  expect(screen.getAllByText(/disponivel/i)).not.toHaveLength(0);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm test -- Pricing.test.tsx IntegrationLogos.test.tsx --run`
Expected: FAIL because the current locale does not provide plan button labels and the integrations component still renders `Em breve`.

- [ ] **Step 3: Commit the failing tests**

```bash
git add frontend/src/features/landing/components/Pricing.test.tsx frontend/src/features/landing/components/IntegrationLogos.test.tsx
git commit -m "test: cover landing pricing and integration regressions"
```

### Task 2: Restore Landing Locale Coverage

**Files:**
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`
- Test: `frontend/src/features/landing/components/IntegrationLogos.test.tsx`

- [ ] **Step 1: Add the missing locale structure**

```json
"plans": {
  "items": {
    "free": {
      "name": "Free",
      "description": "Acesso inicial para conhecer o produto e criar sua rotina.",
      "button": "Comecar gratis",
      "features": ["Chat Basico", "Log de Peso", "Dashboard"]
    },
    "basic": {
      "name": "Basic",
      "description": "Plano para quem quer acompanhamento com memoria e macros.",
      "button": "Assinar Basic",
      "features": ["Memoria AI", "Integracoes", "Analise de Macros"]
    }
  }
},
"integrations_section": {
  "items": {
    "hevy": { "status": "Disponivel" },
    "mfp": { "status": "Disponivel" },
    "zepp": { "status": "Disponivel" }
  }
}
```

- [ ] **Step 2: Fill other missing landing copy referenced by components**

```json
"showcase": {
  "weight_30d": "Peso 30 dias",
  "active_now": "Ativo agora"
},
"conversations": {
  "sofia": {
    "user_1": "Montei meu treino da semana?",
    "trainer_1": "Sim. Ajustei volume e descanso com base na sua recuperacao.",
    "user_2": "E para bater proteina hoje?",
    "trainer_2": "Posso distribuir suas metas em 3 refeicoes e 1 lanche."
  }
},
"footer": {
  "terms": "Termos",
  "privacy": "Privacidade",
  "contact": "Contato",
  "rights": "© {{year}} FityQ. Todos os direitos reservados."
}
```

- [ ] **Step 3: Run the pricing and integration tests**

Run: `cd frontend && npm test -- Pricing.test.tsx IntegrationLogos.test.tsx --run`
Expected: still FAIL or partially fail until the components consume the new structure.

- [ ] **Step 4: Commit the locale coverage**

```bash
git add frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json
git commit -m "feat: complete landing locale coverage"
```

### Task 3: Fix Pricing And Integrations Components

**Files:**
- Modify: `frontend/src/features/landing/components/Pricing.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.tsx`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`
- Test: `frontend/src/features/landing/components/IntegrationLogos.test.tsx`

- [ ] **Step 1: Update `Pricing.tsx` to consume the complete locale contract**

```tsx
const planData = t(`landing.plans.items.${plan.id}`, { returnObjects: true }) as {
  name: string;
  description: string;
  features: string[];
  button: string;
};

<p className="text-sm text-text-secondary min-h-[40px]">
  {planData.description}
</p>

<Button>
  {planData.button}
</Button>
```

- [ ] **Step 2: Replace the fake integration status in `IntegrationLogos.tsx`**

```tsx
const integrations = [
  {
    name: 'Hevy',
    desc: t('landing.integrations_section.hevy_desc'),
    status: t('landing.integrations_section.items.hevy.status'),
    icon: Activity,
  },
];

<span className="text-[10px] font-bold uppercase tracking-widest text-text-muted">
  {item.status}
</span>
```

- [ ] **Step 3: Run the targeted tests**

Run: `cd frontend && npm test -- Pricing.test.tsx IntegrationLogos.test.tsx --run`
Expected: PASS

- [ ] **Step 4: Commit the component fixes**

```bash
git add frontend/src/features/landing/components/Pricing.tsx frontend/src/features/landing/components/IntegrationLogos.tsx
git commit -m "fix: restore landing pricing and integration copy"
```

### Task 4: Lock Remaining Landing Translation Contracts With Tests

**Files:**
- Modify: `frontend/src/features/landing/components/HowItWorks.test.tsx`
- Modify: `frontend/src/features/landing/components/ProductShowcase.test.tsx`
- Modify: `frontend/src/features/landing/components/Footer.test.tsx`
- Test: `frontend/src/features/landing/components/HowItWorks.test.tsx`
- Test: `frontend/src/features/landing/components/ProductShowcase.test.tsx`
- Test: `frontend/src/features/landing/components/Footer.test.tsx`

- [ ] **Step 1: Add failing assertions for the broken translation contracts**

```tsx
it('renders translated step descriptions in how it works', () => {
  render(<HowItWorks />);

  expect(screen.getByText(/sincronize com hevy ou mfp/i)).toBeInTheDocument();
});

it('renders showcase labels driven by locale', () => {
  render(<ProductShowcase />);

  expect(screen.getByText(/peso 30 dias/i)).toBeInTheDocument();
  expect(screen.getByText(/ativo agora/i)).toBeInTheDocument();
});

it('renders localized footer links', () => {
  render(<Footer />);

  expect(screen.getByRole('link', { name: /termos/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /privacidade/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /contato/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npm test -- HowItWorks.test.tsx ProductShowcase.test.tsx Footer.test.tsx --run`
Expected: FAIL because the current locale/component contract does not yet expose those texts correctly.

- [ ] **Step 3: Commit the failing tests**

```bash
git add frontend/src/features/landing/components/HowItWorks.test.tsx frontend/src/features/landing/components/ProductShowcase.test.tsx frontend/src/features/landing/components/Footer.test.tsx
git commit -m "test: cover landing translation contracts"
```

### Task 5: Normalize Remaining Components Against The Locale

**Files:**
- Modify: `frontend/src/features/landing/components/HowItWorks.tsx`
- Modify: `frontend/src/features/landing/components/TrainerShowcase.tsx`
- Modify: `frontend/src/features/landing/components/ChatCarousel.tsx`
- Modify: `frontend/src/features/landing/components/ProductShowcase.tsx`
- Modify: `frontend/src/features/landing/components/Footer.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Test: `frontend/src/features/landing/components/HowItWorks.test.tsx`
- Test: `frontend/src/features/landing/components/ProductShowcase.test.tsx`
- Test: `frontend/src/features/landing/components/Footer.test.tsx`

- [ ] **Step 1: Make `HowItWorks.tsx` read the locale shape correctly**

```tsx
const steps = t('landing.how.steps', { returnObjects: true }) as { title: string; desc: string }[];

<p className="text-text-secondary leading-relaxed">
  {item.desc}
</p>
```

- [ ] **Step 2: Normalize trainer specialties to arrays in the locale**

```json
"profiles": {
  "atlas": {
    "specialties": ["Biomecanica", "Forca", "Performance"]
  }
}
```

- [ ] **Step 3: Add the missing conversation and showcase keys used by `ChatCarousel.tsx` and `ProductShowcase.tsx`**

```json
"conversations": {
  "gymbro": {
    "user_1": "Meu treino de peito ficou fraco hoje.",
    "trainer_1": "Entao vamos subir intensidade sem perder tecnica.",
    "user_2": "Fecha um cardio curto depois?"
  }
}
```

- [ ] **Step 4: Localize the footer links**

```tsx
<a href="#" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
  {t('landing.footer.terms')}
</a>
```

- [ ] **Step 5: Run the remaining targeted tests**

Run: `cd frontend && npm test -- HowItWorks.test.tsx ProductShowcase.test.tsx Footer.test.tsx --run`
Expected: PASS

- [ ] **Step 6: Commit the remaining landing review fixes**

```bash
git add frontend/src/features/landing/components/HowItWorks.tsx frontend/src/features/landing/components/TrainerShowcase.tsx frontend/src/features/landing/components/ChatCarousel.tsx frontend/src/features/landing/components/ProductShowcase.tsx frontend/src/features/landing/components/Footer.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json
git commit -m "fix: align landing components with translated content"
```

### Task 6: Final Landing Verification

**Files:**
- Test: `frontend/src/features/landing/components/*.test.tsx`
- Test: `frontend/src/locales/pt-BR.json`
- Test: `frontend/src/locales/en-US.json`

- [ ] **Step 1: Run the landing component tests**

Run: `cd frontend && npm test -- src/features/landing/components --run`
Expected: PASS

- [ ] **Step 2: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: PASS

- [ ] **Step 3: Run frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit the verification sweep**

```bash
git add frontend/src/features/landing/components frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json
git commit -m "chore: verify landing review changes"
```
