# Landing Page Repositioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposicionar a landing page da FityQ para vender o produto como um sistema de coaching com prova de produto, narrativa aspiracional e foco em cadastro no teste gratis.

**Architecture:** A implementacao preserva a estrutura atual da landing, mas troca a ordem narrativa, a copy e parte dos componentes para refletir provas reais do produto. O trabalho sera guiado por TDD em nivel de componente, seguido por refactor controlado das secoes, atualizacao de locales e validacao final do frontend.

**Tech Stack:** React 19, TypeScript, Vite 7, TailwindCSS v4, React Router 7, Vitest, Testing Library, i18next

---

## Canonical Content Payload

Use este payload como fonte de verdade para a copy da landing. O objetivo do plano e evitar espacos vazios ou decisões abertas durante a implementacao. Se um texto abaixo conflitar com copy antiga, a copy antiga deve ser removida.

### PT-BR

```json
{
  "nav": {
    "demo": "Ver demo",
    "differentiators": "Diferenciais",
    "plans": "Planos",
    "login": "Login"
  },
  "hero": {
    "eyebrow": "Coaching inteligente para a vida real",
    "title": "Transforme sua rotina em evolução consistente.",
    "description": "Treino, nutrição, composição corporal e metabolismo em um sistema de coaching com memória, contexto e orientação prática para o seu dia a dia.",
    "cta": "Começar teste grátis",
    "demo_cta": "Ver demo",
    "proof_1": "Teste grátis",
    "proof_2": "Sem rotina perfeita",
    "proof_3": "Com contexto real"
  },
  "demo": {
    "title": "Veja como o FityQ trabalha no seu dia a dia",
    "subtitle": "Sua rotina gera sinais. O FityQ organiza esse contexto e devolve orientação prática para manter constância sem complicar sua vida.",
    "step_1_eyebrow": "Sua rotina",
    "step_1_title": "Treino, refeição e peso entram no sistema",
    "step_1_description": "Você registra o básico ou importa dados que já usa no dia a dia.",
    "step_2_eyebrow": "O sistema entende",
    "step_2_title": "Tendências e contexto ficam claros",
    "step_2_description": "O FityQ cruza frequência, ingestão, peso e recuperação para enxergar o que mudou.",
    "step_3_eyebrow": "Seu treinador orienta",
    "step_3_title": "Você recebe o próximo passo com clareza",
    "step_3_description": "Em vez de motivação genérica, você recebe uma orientação útil para aquele momento."
  },
  "demo_case": {
    "label": "Exemplo realista",
    "title": "Uma semana comum, tratada com mais inteligência",
    "context_title": "Contexto detectado",
    "context_points": [
      "2 treinos a menos do que o planejado",
      "3 dias acima da meta calórica",
      "Peso oscilando sem tendência clara"
    ],
    "trainer_title": "Resposta do treinador",
    "trainer_name": "Atlas Prime",
    "trainer_reply": "Você não precisa compensar exagerando. Seu melhor movimento hoje é retomar consistência: treino curto, proteína alta e meta calórica simples de cumprir."
  },
  "how": {
    "title": "Como funciona na prática",
    "subtitle": "Menos adivinhação. Mais clareza sobre o que fazer hoje.",
    "steps": [
      {
        "title": "Seus dados entram",
        "desc": "Treinos, refeições, peso e composição corporal entram manualmente ou por importação."
      },
      {
        "title": "O sistema organiza sinais e tendências",
        "desc": "O FityQ transforma rotina dispersa em contexto claro sobre constância, balanço e progresso."
      },
      {
        "title": "Você recebe orientação prática",
        "desc": "Seu treinador usa memória e contexto para responder com clareza, sem conselho genérico."
      }
    ]
  },
  "showcase": {
    "title": "Sistema operacional da sua evolução",
    "description": "Painel, chat e leitura metabólica trabalhando juntos para transformar sua rotina em clareza prática.",
    "dashboard_title": "Dashboard",
    "dashboard_subtitle": "Vários sinais, uma leitura só",
    "chat_title": "Chat com contexto",
    "chat_subtitle": "Orientação que entende sua semana",
    "metabolism_title": "Metabolismo adaptativo",
    "metabolism_subtitle": "Menos fórmula fixa, mais realidade",
    "widgets": {
      "daily_target": "Meta diária",
      "metabolic_confidence": "Confiança metabólica",
      "weight": "Peso",
      "fat": "Gordura",
      "muscle": "Massa muscular",
      "calories": "Calorias",
      "recent_activity": "Atividade recente",
      "weekly_frequency": "Frequência semanal",
      "prs": "PRs recentes",
      "strength_radar": "Radar de força"
    },
    "chat_example_user": "Treinei menos esta semana e saí da meta em alguns dias. O que faz mais sentido hoje?",
    "chat_example_trainer": "Hoje o foco não é compensar no radicalismo. Vamos proteger a constância com treino curto, proteína alta e uma meta simples de cumprir.",
    "metabolism_stats": {
      "target": "Meta diária",
      "confidence": "Confiança",
      "balance": "Balanço energético",
      "trend": "Tendência semanal",
      "consistency": "Consistência",
      "stability": "Estabilidade calórica"
    }
  },
  "trainers": {
    "title": "Escolha o estilo de acompanhamento que combina com você",
    "description": "Cada mentor lê o mesmo contexto com uma personalidade diferente. Você escolhe quem mais combina com a forma como gosta de evoluir.",
    "cta": "Começar com este mentor",
    "profiles": {
      "atlas": {
        "for_who": "Para quem gosta de clareza e decisões guiadas por dados.",
        "style": "Direto, analítico e preciso.",
        "best_for": "Ajustes de treino, leitura de progresso e organização da rotina.",
        "example": "Seu progresso melhora mais com consistência simples do que com correções extremas."
      },
      "luna": {
        "for_who": "Para quem busca constância com mais leveza e equilíbrio.",
        "style": "Calma, acolhedora e orientada a bem-estar.",
        "best_for": "Rotina sustentável, recuperação e reconexão com hábitos.",
        "example": "Hoje o melhor passo é reduzir a pressão e proteger o ritmo que você consegue manter."
      },
      "sofia": {
        "for_who": "Para quem valoriza contexto fisiológico e leitura metabólica.",
        "style": "Empática, técnica e cuidadosa.",
        "best_for": "Metabolismo, saúde feminina e ajustes de rotina com mais contexto.",
        "example": "Antes de apertar a dieta, precisamos entender o que essa semana realmente sinaliza."
      },
      "sargento": {
        "for_who": "Para quem responde melhor a cobrança e estrutura firme.",
        "style": "Intenso, disciplinado e sem rodeios.",
        "best_for": "Disciplina, aderência e execução.",
        "example": "Seu plano não precisa ser mais complicado. Precisa ser cumprido."
      },
      "gymbro": {
        "for_who": "Para quem quer incentivo, energia e parceria.",
        "style": "Motivador, próximo e fácil de acompanhar.",
        "best_for": "Constância, confiança e rotina sem peso excessivo.",
        "example": "Bora voltar para o básico bem feito. É isso que constrói resultado de verdade."
      }
    }
  },
  "diff": {
    "title": "Por que o FityQ é diferente",
    "subtitle": "Não é só um chat. É um sistema que transforma sua rotina em contexto útil.",
    "features": {
      "memory": {
        "title": "Memória que aprende com sua rotina",
        "description": "O sistema lembra do que vem acontecendo para responder com mais contexto."
      },
      "metabolism": {
        "title": "Leitura metabólica adaptativa",
        "description": "Seu metabolismo deixa de ser uma fórmula fixa e passa a refletir seus dados reais."
      },
      "dashboard": {
        "title": "Dashboard com sinais que se conectam",
        "description": "Peso, gordura, músculo, calorias, atividade e frequência no mesmo lugar."
      },
      "trainers": {
        "title": "Mentores com estilos diferentes",
        "description": "O mesmo contexto pode virar orientações diferentes, de acordo com o perfil que mais combina com você."
      },
      "integrations": {
        "title": "Integrações e importações reais",
        "description": "Use o que você já registra para acelerar a utilidade do sistema."
      },
      "multichannel": {
        "title": "Acompanhamento além do app",
        "description": "No plano Pro, você também pode usar imagem no chat e acesso via Telegram."
      }
    }
  },
  "integrations_section": {
    "title": "Traga sua rotina para dentro do sistema",
    "subtitle": "Quanto mais contexto entra, mais útil fica a orientação.",
    "hevy_desc": "Importe ou sincronize seus treinos para transformar execução em contexto.",
    "mfp_desc": "Traga seu histórico alimentar para conectar ingestão e progresso.",
    "zepp_desc": "Use dados de peso e composição corporal para enriquecer a leitura do sistema."
  },
  "plans": {
    "title": "Comece simples. Evolua com contexto.",
    "subtitle": "O teste grátis existe para você sentir o sistema funcionando na sua rotina antes de decidir."
  },
  "faq": {
    "title": "FAQ",
    "items": [
      {
        "q": "Preciso conectar apps para funcionar?",
        "a": "Não. Você pode começar registrando manualmente e adicionar integrações depois."
      },
      {
        "q": "Funciona se eu não tiver rotina perfeita?",
        "a": "Sim. A proposta é justamente ajudar você a manter constância no mundo real, não exigir perfeição."
      },
      {
        "q": "Como a memória funciona?",
        "a": "O FityQ usa o histórico da sua rotina para responder com mais contexto e continuidade ao longo do tempo."
      },
      {
        "q": "Como o metabolismo é calculado?",
        "a": "A leitura metabólica usa seus dados de peso e nutrição para produzir uma estimativa adaptativa, em vez de depender apenas de fórmulas fixas."
      },
      {
        "q": "Qual a diferença entre os planos?",
        "a": "O teste grátis permite experimentar a proposta. Os planos pagos ampliam volume de uso, acesso a mentores e recursos como imagens, integrações e Telegram."
      },
      {
        "q": "Posso cancelar a qualquer momento?",
        "a": "Sim. Você pode interromper sua assinatura sem contrato de longo prazo."
      },
      {
        "q": "O FityQ substitui orientação médica ou nutricional?",
        "a": "Não. O produto oferece apoio digital para rotina, hábitos e performance, mas não substitui acompanhamento profissional individualizado."
      },
      {
        "q": "Onde posso ler sobre privacidade e termos de uso?",
        "a": "Os links para Política de Privacidade e Termos de Uso ficam disponíveis na landing e no rodapé."
      }
    ]
  },
  "cta": {
    "title": "Comece a construir uma rotina mais inteligente",
    "subtitle": "Teste o FityQ e veja como sua rotina pode virar clareza, contexto e constância.",
    "button": "Começar teste grátis",
    "trial": "Teste sem compromisso."
  }
}
```

### EN-US

```json
{
  "hero": {
    "eyebrow": "Intelligent coaching for real life",
    "title": "Turn your routine into consistent progress.",
    "description": "Training, nutrition, body composition, and metabolism in one coaching system with memory, context, and practical guidance for everyday life.",
    "cta": "Start free trial",
    "demo_cta": "See demo"
  },
  "demo": {
    "title": "See how FityQ works in everyday life",
    "subtitle": "Your routine creates signals. FityQ organizes that context and turns it into practical guidance you can actually follow."
  },
  "showcase": {
    "title": "The operating system for your progress",
    "description": "Dashboard, chat, and metabolic insight working together to turn your routine into practical clarity."
  },
  "trainers": {
    "title": "Choose the coaching style that fits you",
    "description": "Each mentor reads the same context with a different personality. You choose the one that matches how you like to grow."
  },
  "diff": {
    "title": "Why FityQ feels different",
    "subtitle": "It is not just a chat. It is a system that turns your routine into useful context."
  },
  "integrations_section": {
    "title": "Bring your routine into the system",
    "subtitle": "The more context goes in, the more useful the guidance becomes."
  },
  "plans": {
    "title": "Start simple. Grow with context.",
    "subtitle": "The free trial exists so you can feel the system working in your routine before deciding."
  },
  "cta": {
    "title": "Start building a smarter routine",
    "subtitle": "Try FityQ and see how your routine can turn into clarity, context, and consistency.",
    "button": "Start free trial",
    "trial": "No commitment."
  }
}
```

### ES-ES

```json
{
  "hero": {
    "eyebrow": "Coaching inteligente para la vida real",
    "title": "Convierte tu rutina en progreso constante.",
    "description": "Entrenamiento, nutricion, composicion corporal y metabolismo en un sistema de coaching con memoria, contexto y orientacion practica para tu dia a dia.",
    "cta": "Empezar prueba gratis",
    "demo_cta": "Ver demo"
  },
  "demo": {
    "title": "Mira como FityQ trabaja en tu dia a dia",
    "subtitle": "Tu rutina genera senales. FityQ organiza ese contexto y lo convierte en una orientacion practica que realmente puedes seguir."
  },
  "showcase": {
    "title": "El sistema operativo de tu progreso",
    "description": "Panel, chat y lectura metabolica trabajando juntos para transformar tu rutina en claridad practica."
  },
  "trainers": {
    "title": "Elige el estilo de acompanamiento que encaja contigo",
    "description": "Cada mentor interpreta el mismo contexto con una personalidad distinta. Tu eliges el que mejor encaja con tu forma de avanzar."
  },
  "diff": {
    "title": "Por que FityQ se siente diferente",
    "subtitle": "No es solo un chat. Es un sistema que convierte tu rutina en contexto util."
  },
  "integrations_section": {
    "title": "Lleva tu rutina dentro del sistema",
    "subtitle": "Cuanto mas contexto entra, mas util se vuelve la orientacion."
  },
  "plans": {
    "title": "Empieza simple. Avanza con contexto.",
    "subtitle": "La prueba gratis existe para que sientas el sistema funcionando en tu rutina antes de decidir."
  },
  "cta": {
    "title": "Empieza a construir una rutina mas inteligente",
    "subtitle": "Prueba FityQ y mira como tu rutina puede convertirse en claridad, contexto y constancia.",
    "button": "Empezar prueba gratis",
    "trial": "Sin compromiso."
  }
}
```

### Canonical Mentor Demo Replies

Use estes exemplos em cards expandidos, tooltips ou microdemos. Nao inventar novas respostas durante implementacao sem motivo.

```json
{
  "atlas": "Seu progresso melhora mais com consistencia simples do que com correcoes extremas.",
  "luna": "Hoje o melhor passo e reduzir a pressao e proteger o ritmo que voce consegue manter.",
  "sofia": "Antes de apertar a dieta, precisamos entender o que essa semana realmente sinaliza.",
  "sargento": "Seu plano nao precisa ser mais complicado. Precisa ser cumprido.",
  "gymbro": "Bora voltar para o basico bem feito. E isso que constroi resultado de verdade."
}
```

### Canonical Product Demo Conversation

Use esta conversa como base para o painel de chat da showcase:

```json
{
  "user": "Treinei menos esta semana e sai da meta em alguns dias. O que faz mais sentido hoje?",
  "trainer": "Hoje o foco nao e compensar no radicalismo. Vamos proteger a constancia com treino curto, proteina alta e uma meta simples de cumprir."
}
```

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
  "eyebrow": "Coaching inteligente para a vida real",
  "title": "Transforme sua rotina em evolucao consistente.",
  "description": "Treino, nutricao, composicao corporal e metabolismo em um sistema de coaching com memoria, contexto e orientacao pratica para o seu dia a dia.",
  "cta": "Comecar teste gratis",
  "demo_cta": "Ver demo",
  "proof_1": "Teste gratis",
  "proof_2": "Sem rotina perfeita",
  "proof_3": "Com contexto real"
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
    {
      "eyebrow": "Sua rotina",
      "title": "Treino, refeicao e peso entram no sistema",
      "description": "Voce registra o basico ou importa dados que ja usa no dia a dia."
    },
    {
      "eyebrow": "O sistema entende",
      "title": "Tendencias e contexto ficam claros",
      "description": "O FityQ cruza frequencia, ingestao, peso e recuperacao para enxergar o que mudou."
    },
    {
      "eyebrow": "Seu treinador orienta",
      "title": "Voce recebe o proximo passo com clareza",
      "description": "Em vez de motivacao generica, voce recebe uma orientacao util para aquele momento."
    }
  ]
}
```

- [ ] **Step 4.1: Add exact demo-case content in locales**

```json
"demo_case": {
  "label": "Exemplo realista",
  "title": "Uma semana comum, tratada com mais inteligencia",
  "context_title": "Contexto detectado",
  "context_points": [
    "2 treinos a menos do que o planejado",
    "3 dias acima da meta calorica",
    "Peso oscilando sem tendencia clara"
  ],
  "trainer_title": "Resposta do treinador",
  "trainer_name": "Atlas Prime",
  "trainer_reply": "Voce nao precisa compensar exagerando. Seu melhor movimento hoje e retomar consistencia: treino curto, proteina alta e meta calorica simples de cumprir."
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
  "dashboard_title": "Dashboard",
  "dashboard_subtitle": "Varios sinais, uma leitura so",
  "chat_title": "Chat com contexto",
  "chat_subtitle": "Orientacao que entende sua semana",
  "metabolism_title": "Metabolismo adaptativo",
  "metabolism_subtitle": "Menos formula fixa, mais realidade",
  "widgets": {
    "daily_target": "Meta diaria",
    "metabolic_confidence": "Confianca metabolica",
    "weight": "Peso",
    "fat": "Gordura",
    "muscle": "Massa muscular",
    "calories": "Calorias",
    "recent_activity": "Atividade recente",
    "weekly_frequency": "Frequencia semanal",
    "prs": "PRs recentes",
    "strength_radar": "Radar de forca"
  },
  "chat_example_user": "Treinei menos esta semana e sai da meta em alguns dias. O que faz mais sentido hoje?",
  "chat_example_trainer": "Hoje o foco nao e compensar no radicalismo. Vamos proteger a constancia com treino curto, proteina alta e uma meta simples de cumprir.",
  "metabolism_stats": {
    "target": "Meta diaria",
    "confidence": "Confianca",
    "balance": "Balanco energetico",
    "trend": "Tendencia semanal",
    "consistency": "Consistencia",
    "stability": "Estabilidade calorica"
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

- [ ] **Step 3.1: Add exact mentor card payload**

```json
"profiles": {
  "atlas": {
    "for_who": "Para quem gosta de clareza e decisoes guiadas por dados.",
    "style": "Direto, analitico e preciso.",
    "best_for": "Ajustes de treino, leitura de progresso e organizacao da rotina.",
    "example": "Seu progresso melhora mais com consistencia simples do que com correcoes extremas."
  },
  "luna": {
    "for_who": "Para quem busca constancia com mais leveza e equilibrio.",
    "style": "Calma, acolhedora e orientada a bem-estar.",
    "best_for": "Rotina sustentavel, recuperacao e reconexao com habitos.",
    "example": "Hoje o melhor passo e reduzir a pressao e proteger o ritmo que voce consegue manter."
  },
  "sofia": {
    "for_who": "Para quem valoriza contexto fisiologico e leitura metabolica.",
    "style": "Empatica, tecnica e cuidadosa.",
    "best_for": "Metabolismo, saude feminina e ajustes de rotina com mais contexto.",
    "example": "Antes de apertar a dieta, precisamos entender o que essa semana realmente sinaliza."
  },
  "sargento": {
    "for_who": "Para quem responde melhor a cobranca e estrutura firme.",
    "style": "Intenso, disciplinado e sem rodeios.",
    "best_for": "Disciplina, aderencia e execucao.",
    "example": "Seu plano nao precisa ser mais complicado. Precisa ser cumprido."
  },
  "gymbro": {
    "for_who": "Para quem quer incentivo, energia e parceria.",
    "style": "Motivador, proximo e facil de acompanhar.",
    "best_for": "Constancia, confianca e rotina sem peso excessivo.",
    "example": "Bora voltar para o basico bem feito. E isso que constroi resultado de verdade."
  }
}
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
    {
      "q": "Preciso conectar apps para funcionar?",
      "a": "Nao. Voce pode comecar registrando manualmente e adicionar integracoes depois."
    },
    {
      "q": "Funciona se eu nao tiver rotina perfeita?",
      "a": "Sim. A proposta e justamente ajudar voce a manter constancia no mundo real, nao exigir perfeicao."
    },
    {
      "q": "Como a memoria funciona?",
      "a": "O FityQ usa o historico da sua rotina para responder com mais contexto e continuidade ao longo do tempo."
    },
    {
      "q": "Como o metabolismo e calculado?",
      "a": "A leitura metabolica usa seus dados de peso e nutricao para produzir uma estimativa adaptativa, em vez de depender apenas de formulas fixas."
    },
    {
      "q": "Qual a diferenca entre os planos?",
      "a": "O teste gratis permite experimentar a proposta. Os planos pagos ampliam volume de uso, acesso a mentores e recursos como imagens, integracoes e Telegram."
    },
    {
      "q": "Posso cancelar a qualquer momento?",
      "a": "Sim. Voce pode interromper sua assinatura sem contrato de longo prazo."
    },
    {
      "q": "O FityQ substitui orientacao medica ou nutricional?",
      "a": "Nao. O produto oferece apoio digital para rotina, habitos e performance, mas nao substitui acompanhamento profissional individualizado."
    },
    {
      "q": "Onde posso ler sobre privacidade e termos de uso?",
      "a": "Os links para Politica de Privacidade e Termos de Uso ficam disponiveis na landing e no rodape."
    }
  ]
}
```

- [ ] **Step 5.1: Replace differentiator locale contract with exact copy**

```json
"diff": {
  "title": "Por que o FityQ e diferente",
  "subtitle": "Nao e so um chat. E um sistema que transforma sua rotina em contexto util.",
  "features": {
    "memory": {
      "title": "Memoria que aprende com sua rotina",
      "description": "O sistema lembra do que vem acontecendo para responder com mais contexto."
    },
    "metabolism": {
      "title": "Leitura metabolica adaptativa",
      "description": "Seu metabolismo deixa de ser uma formula fixa e passa a refletir seus dados reais."
    },
    "dashboard": {
      "title": "Dashboard com sinais que se conectam",
      "description": "Peso, gordura, musculo, calorias, atividade e frequencia no mesmo lugar."
    },
    "trainers": {
      "title": "Mentores com estilos diferentes",
      "description": "O mesmo contexto pode virar orientacoes diferentes, de acordo com o perfil que mais combina com voce."
    },
    "integrations": {
      "title": "Integracoes e importacoes reais",
      "description": "Use o que voce ja registra para acelerar a utilidade do sistema."
    },
    "multichannel": {
      "title": "Acompanhamento alem do app",
      "description": "No plano Pro, voce tambem pode usar imagem no chat e acesso via Telegram."
    }
  }
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
