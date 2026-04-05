# Landing Page Repositioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposicionar a landing page da FityQ para vender o produto como um sistema de coaching com prova de produto, narrativa aspiracional e foco em cadastro no teste gratis.

**Architecture:** A implementacao preserva a estrutura atual da landing, mas troca a ordem narrativa, a copy e parte dos componentes para refletir provas reais do produto. O trabalho sera guiado por TDD em nivel de componente, seguido por refactor controlado das secoes, atualizacao de locales e validacao final do frontend.

**Tech Stack:** React 19, TypeScript, Vite 7, TailwindCSS v4, React Router 7, Vitest, Testing Library, i18next

---

### Task 1: Redefine Footer and Trust Entry Points

**Files:**
- Modify: `frontend/src/features/landing/components/Footer.tsx`
- Modify: `frontend/src/features/landing/components/Footer.test.tsx`
- Modify: `frontend/src/features/landing/components/Hero.tsx`
- Modify: `frontend/src/features/landing/components/Hero.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

- [ ] **Step 1: Write the failing tests for legal links and hero CTAs**

```tsx
it('links to terms and privacy from the footer', () => {
  render(<Footer />);

  expect(screen.getByRole('link', { name: /termos/i })).toHaveAttribute('href', '/termos-de-uso');
  expect(screen.getByRole('link', { name: /privacidade/i })).toHaveAttribute('href', '/politica-de-privacidade');
});

it('renders the new hero positioning and secondary demo CTA', () => {
  render(<Hero />);

  expect(screen.getByText(/Transforme sua rotina em evolu[cç][aã]o consistente/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Ver demo/i })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted landing tests and confirm they fail**

Run: `cd frontend && npm test -- Hero.test.tsx Footer.test.tsx --runInBand`
Expected: FAIL because the old hero copy and footer `href="#"` links do not satisfy the new assertions.

- [ ] **Step 3: Implement footer links and hero trust bar / CTA copy**

```tsx
<a href="/termos-de-uso" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
  {t('landing.footer.terms')}
</a>
<a href="/politica-de-privacidade" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
  {t('landing.footer.privacy')}
</a>
```

```tsx
<h1 className="font-display text-4xl sm:text-6xl font-bold text-text-primary mb-6 leading-tight tracking-tight">
  {t('landing.hero.title')}
</h1>

<div className="flex flex-col sm:flex-row gap-4">
  <Button onClick={() => { void navigate('/login?mode=register'); }} variant="primary" size="lg">
    {t('landing.hero.cta')}
  </Button>

  <Button
    onClick={() => {
      document.querySelector('#demo')?.scrollIntoView({ behavior: 'smooth' });
    }}
    variant="secondary"
    size="lg"
  >
    {t('landing.hero.demo_cta')}
  </Button>
</div>

<div className="mt-8 flex flex-wrap gap-4 text-sm text-text-muted">
  <span>{t('landing.trust_badge_free')}</span>
  <a href="/politica-de-privacidade">{t('landing.footer.privacy')}</a>
  <a href="/termos-de-uso">{t('landing.footer.terms')}</a>
</div>
```

- [ ] **Step 4: Update translations to the new hero contract**

```json
"hero": {
  "title": "Transforme sua rotina em evolucao consistente.",
  "description": "Treino, nutricao, composicao corporal e metabolismo em um sistema de coaching com memoria, contexto e orientacao pratica para o seu dia a dia.",
  "cta": "Comecar teste gratis",
  "demo_cta": "Ver demo"
}
```

- [ ] **Step 5: Run the targeted tests again**

Run: `cd frontend && npm test -- Hero.test.tsx Footer.test.tsx --runInBand`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/landing/components/Hero.tsx frontend/src/features/landing/components/Hero.test.tsx frontend/src/features/landing/components/Footer.tsx frontend/src/features/landing/components/Footer.test.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json
git commit -m "feat: add landing trust entry points"
```

### Task 2: Replace Fake Conversation Demo With Product-Proof Demo

**Files:**
- Modify: `frontend/src/features/landing/components/ChatCarousel.tsx`
- Modify: `frontend/src/features/landing/components/ChatCarousel.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

- [ ] **Step 1: Write the failing tests for the new demo section**

```tsx
it('renders the product-proof demo section', () => {
  render(<ChatCarousel />);

  expect(screen.getByText(/Veja como o FityQ trabalha no seu dia a dia/i)).toBeInTheDocument();
  expect(screen.getByText(/Sua rotina/i)).toBeInTheDocument();
  expect(screen.getByText(/O sistema entende/i)).toBeInTheDocument();
  expect(screen.getByText(/Seu treinador orienta/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted test to verify failure**

Run: `cd frontend && npm test -- ChatCarousel.test.tsx --runInBand`
Expected: FAIL because the component still renders the old "Experimente agora" simulated conversations.

- [ ] **Step 3: Replace the rotating fake chat with a proof-of-product scenario**

```tsx
<section id="demo" className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border">
  <div className="max-w-6xl mx-auto">
    <div className="text-center mb-12">
      <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
        {t('landing.demo.title')}
      </h2>
      <p className="text-lg text-text-secondary max-w-3xl mx-auto">
        {t('landing.demo.subtitle')}
      </p>
    </div>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {steps.map((step) => (
        <div key={step.title} className="rounded-2xl border border-border bg-light-bg p-6">
          <p className="text-xs font-bold uppercase tracking-widest text-primary mb-3">{step.eyebrow}</p>
          <h3 className="text-xl font-bold text-text-primary mb-3">{step.title}</h3>
          <p className="text-sm text-text-secondary leading-relaxed">{step.description}</p>
        </div>
      ))}
    </div>
  </div>
</section>
```

- [ ] **Step 4: Add the new demo locale schema in all three languages**

```json
"demo": {
  "title": "Veja como o FityQ trabalha no seu dia a dia",
  "subtitle": "Sua rotina gera sinais. O FityQ organiza esse contexto e devolve orientacao pratica para manter constancia.",
  "steps": [
    { "eyebrow": "Sua rotina", "title": "Treino, refeicao e peso entram no sistema", "description": "..." },
    { "eyebrow": "O sistema entende", "title": "Tendencias e contexto ficam claros", "description": "..." },
    { "eyebrow": "Seu treinador orienta", "title": "Voce recebe o proximo passo com clareza", "description": "..." }
  ]
}
```

- [ ] **Step 5: Re-run the demo test**

Run: `cd frontend && npm test -- ChatCarousel.test.tsx --runInBand`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/landing/components/ChatCarousel.tsx frontend/src/features/landing/components/ChatCarousel.test.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json
git commit -m "feat: replace landing fake chat with product demo"
```

### Task 3: Rebuild the Product Narrative Sections

**Files:**
- Modify: `frontend/src/features/landing/components/ProductShowcase.tsx`
- Modify: `frontend/src/features/landing/components/ProductShowcase.test.tsx`
- Modify: `frontend/src/features/landing/components/HowItWorks.tsx`
- Modify: `frontend/src/features/landing/components/HowItWorks.test.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.tsx`
- Modify: `frontend/src/features/landing/components/IntegrationLogos.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

- [ ] **Step 1: Write the failing tests for the new section messaging**

```tsx
it('renders the dashboard as a real multi-widget control center', () => {
  render(<ProductShowcase />);

  expect(screen.getByText(/Sistema operacional da sua evolu[cç][aã]o/i)).toBeInTheDocument();
  expect(screen.getByText(/confianca metabolica/i)).toBeInTheDocument();
  expect(screen.getByText(/atividade recente/i)).toBeInTheDocument();
});

it('renders the practical three-step flow', () => {
  render(<HowItWorks />);

  expect(screen.getByText(/Seus dados entram/i)).toBeInTheDocument();
  expect(screen.getByText(/O sistema organiza sinais e tend[eê]ncias/i)).toBeInTheDocument();
});

it('positions integrations as context input, not generic logos', () => {
  render(<IntegrationLogos />);

  expect(screen.getByText(/Traga sua rotina para dentro do sistema/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted tests and confirm failure**

Run: `cd frontend && npm test -- ProductShowcase.test.tsx HowItWorks.test.tsx IntegrationLogos.test.tsx --runInBand`
Expected: FAIL because the old copy and structure are still in place.

- [ ] **Step 3: Rewrite `ProductShowcase` around dashboard, chat, and metabolism proofs**

```tsx
<h2 className="font-display text-3xl font-bold text-text-primary mb-4">
  {t('landing.showcase.title')}
</h2>
<p className="text-lg text-text-secondary max-w-3xl mx-auto">
  {t('landing.showcase.description')}
</p>
```

```tsx
const dashboardHighlights = [
  t('landing.showcase.widgets.daily_target'),
  t('landing.showcase.widgets.metabolic_confidence'),
  t('landing.showcase.widgets.recent_activity'),
  t('landing.showcase.widgets.weekly_frequency'),
  t('landing.showcase.widgets.prs'),
  t('landing.showcase.widgets.strength_radar'),
];
```

- [ ] **Step 4: Rewrite `HowItWorks` and `IntegrationLogos` to fit the approved story**

```tsx
const steps = t('landing.how.steps', { returnObjects: true }) as { title: string; desc: string }[];
```

```tsx
const integrations = [
  { name: 'Hevy', desc: t('landing.integrations_section.hevy_desc') },
  { name: 'MyFitnessPal', desc: t('landing.integrations_section.mfp_desc') },
  { name: 'Zepp Life', desc: t('landing.integrations_section.zepp_desc') },
];
```

- [ ] **Step 5: Update all locale keys used by those sections**

```json
"showcase": {
  "title": "Sistema operacional da sua evolucao",
  "description": "Painel, chat e leitura metabolica trabalhando juntos para transformar sua rotina em clareza pratica.",
  "widgets": {
    "daily_target": "Meta diaria",
    "metabolic_confidence": "Confianca metabolica",
    "recent_activity": "Atividade recente",
    "weekly_frequency": "Frequencia semanal",
    "prs": "PRs recentes",
    "strength_radar": "Radar de forca"
  }
}
```

- [ ] **Step 6: Re-run the targeted tests**

Run: `cd frontend && npm test -- ProductShowcase.test.tsx HowItWorks.test.tsx IntegrationLogos.test.tsx --runInBand`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/landing/components/ProductShowcase.tsx frontend/src/features/landing/components/ProductShowcase.test.tsx frontend/src/features/landing/components/HowItWorks.tsx frontend/src/features/landing/components/HowItWorks.test.tsx frontend/src/features/landing/components/IntegrationLogos.tsx frontend/src/features/landing/components/IntegrationLogos.test.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json
git commit -m "feat: rebuild landing product narrative sections"
```

### Task 4: Reframe Mentors, Differentiators, and FAQ

**Files:**
- Modify: `frontend/src/features/landing/components/TrainerShowcase.tsx`
- Modify: `frontend/src/features/landing/components/TrainerShowcase.test.tsx`
- Modify: `frontend/src/features/landing/components/Features.tsx`
- Modify: `frontend/src/features/landing/components/Features.test.tsx`
- Modify: `frontend/src/features/landing/components/FAQ.tsx`
- Modify: `frontend/src/features/landing/components/FAQ.test.tsx`
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

- [ ] **Step 1: Write the failing tests for the reframed sections**

```tsx
it('presents mentors as coaching styles, not generic characters', () => {
  render(<TrainerShowcase />);

  expect(screen.getByText(/Escolha o estilo de acompanhamento que combina com voc[eê]/i)).toBeInTheDocument();
});

it('only shows real differentiators', () => {
  render(<Features />);

  expect(screen.getByText(/Mem[óo]ria que aprende com sua rotina/i)).toBeInTheDocument();
  expect(screen.queryByText(/Vis[aã]o Computacional/i)).not.toBeInTheDocument();
});

it('answers onboarding objections in the faq', () => {
  render(<FAQ />);

  expect(screen.getByText(/Preciso conectar apps para funcionar/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted tests and verify failure**

Run: `cd frontend && npm test -- TrainerShowcase.test.tsx Features.test.tsx FAQ.test.tsx --runInBand`
Expected: FAIL because the old sections still contain generic mentor copy, old differentiators, and weak FAQ.

- [ ] **Step 3: Rework `TrainerShowcase` to emphasize fit and coaching style**

```tsx
<p className="text-lg text-text-secondary max-w-3xl mx-auto">
  {t('landing.trainers.description')}
</p>
```

```json
"description": "Escolha o estilo de acompanhamento que combina com voce e com a forma como gosta de evoluir."
```

- [ ] **Step 4: Replace fake differentiators with real product capabilities**

```tsx
const features = [
  {
    icon: Brain,
    title: t('landing.diff.features.memory.title'),
    description: t('landing.diff.features.memory.description'),
  },
  {
    icon: Zap,
    title: t('landing.diff.features.metabolism.title'),
    description: t('landing.diff.features.metabolism.description'),
  },
  {
    icon: LayoutGrid,
    title: t('landing.diff.features.dashboard.title'),
    description: t('landing.diff.features.dashboard.description'),
  },
];
```

- [ ] **Step 5: Replace the FAQ items in all locales with real objection handling**

```json
"faq": {
  "title": "FAQ",
  "items": [
    { "q": "Preciso conectar apps para funcionar?", "a": "Nao. Voce pode comecar manualmente e adicionar integracoes depois." },
    { "q": "Funciona se eu nao tiver rotina perfeita?", "a": "Sim. O foco e ajudar voce a manter constancia no mundo real." }
  ]
}
```

- [ ] **Step 6: Re-run the targeted tests**

Run: `cd frontend && npm test -- TrainerShowcase.test.tsx Features.test.tsx FAQ.test.tsx --runInBand`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/landing/components/TrainerShowcase.tsx frontend/src/features/landing/components/TrainerShowcase.test.tsx frontend/src/features/landing/components/Features.tsx frontend/src/features/landing/components/Features.test.tsx frontend/src/features/landing/components/FAQ.tsx frontend/src/features/landing/components/FAQ.test.tsx frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json
git commit -m "feat: reframe landing mentors differentiators and faq"
```

### Task 5: Reorder the Page and Align Navigation to the New Funnel

**Files:**
- Modify: `frontend/src/features/landing/LandingPage.tsx`
- Modify: `frontend/src/features/landing/LandingPage.test.tsx`
- Modify: `frontend/src/features/landing/components/Navbar.tsx`
- Modify: `frontend/src/features/landing/components/Navbar.test.tsx`

- [ ] **Step 1: Write the failing tests for the new funnel order and navigation emphasis**

```tsx
it('renders the landing with the demo before plans and faq', () => {
  render(<LandingPage />);

  const sections = screen.getAllByRole('main')[0].textContent ?? '';
  expect(sections.indexOf('Ver demo')).toBeLessThan(sections.indexOf('Planos'));
});

it('keeps navigation focused on demo, value, and plans', () => {
  render(<Navbar />);

  expect(screen.getByText(/Diferenciais/i)).toBeInTheDocument();
  expect(screen.getByText(/Planos/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the targeted tests and confirm failure**

Run: `cd frontend && npm test -- LandingPage.test.tsx Navbar.test.tsx --runInBand`
Expected: FAIL because the page order and nav emphasis still reflect the old landing.

- [ ] **Step 3: Reorder `LandingPage` to match the approved funnel**

```tsx
<main>
  <Hero />
  <ChatCarousel />
  <HowItWorks />
  <ProductShowcase />
  <TrainerShowcase />
  <Features />
  <IntegrationLogos />
  <Pricing />
  <FAQ />
  <FinalCTA />
</main>
```

- [ ] **Step 4: Adjust navbar anchor map to reflect the new journey**

```tsx
const navLinks = [
  { name: t('landing.nav.demo'), href: '#demo' },
  { name: t('landing.nav.differentiators'), href: '#diferenciais' },
  { name: t('landing.nav.plans'), href: '#planos' },
];
```

- [ ] **Step 5: Re-run the targeted tests**

Run: `cd frontend && npm test -- LandingPage.test.tsx Navbar.test.tsx --runInBand`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/landing/LandingPage.tsx frontend/src/features/landing/LandingPage.test.tsx frontend/src/features/landing/components/Navbar.tsx frontend/src/features/landing/components/Navbar.test.tsx
git commit -m "feat: align landing order with conversion funnel"
```

### Task 6: Run Final Frontend Verification

**Files:**
- Verify: `frontend/src/features/landing/**/*`
- Verify: `frontend/src/locales/*.json`

- [ ] **Step 1: Run the full landing-related test slice**

Run: `cd frontend && npm test -- landing --runInBand`
Expected: PASS

- [ ] **Step 2: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: PASS

- [ ] **Step 3: Run frontend typecheck**

Run: `cd frontend && npm run typecheck`
Expected: PASS

- [ ] **Step 4: Inspect the diff for locale completeness and section integrity**

Run: `git diff -- frontend/src/features/landing frontend/src/locales`
Expected: all new visible text exists in `pt-BR`, `en-US`, and `es-ES`, and no stale fake-claim copy remains in touched landing files.

- [ ] **Step 5: Commit final verification-safe state**

```bash
git add frontend/src/features/landing frontend/src/locales
git commit -m "feat: ship landing repositioning"
```
