# Landing Review Design

## Goal

Corrigir a landing page pública para que todo o conteúdo renderizado esteja traduzido, coerente com o produto atual e alinhado com as integrações e planos realmente disponíveis.

## Current Findings

- `frontend/src/features/landing/components/Pricing.tsx` espera `description` e `button` em `landing.plans.items.*`, mas essas chaves não existem hoje em `frontend/src/locales/pt-BR.json` nem em `frontend/src/locales/en-US.json`. Isso faz os cards de pricing renderizarem descrição e CTA vazios.
- `frontend/src/features/landing/components/IntegrationLogos.tsx` marca todas as integrações com `landing.integrations_section.coming_soon`, apesar do app já suportar Hevy, importação de MyFitnessPal e importação de Zepp Life.
- Há outros desalinhamentos entre componentes e locale na landing:
  - `HowItWorks.tsx` lê `description`, mas o locale expõe `desc`.
  - `TrainerShowcase.tsx` e `ChatCarousel.tsx` fazem cast de `specialties` para `string[]`, mas o locale atual guarda `specialties` como string simples.
  - `ProductShowcase.tsx` referencia chaves inexistentes como `landing.showcase.weight_30d` e `landing.conversations.*`.
  - `Footer.tsx` mantém links hardcoded em inglês fora do i18n.

## Approach

Tratar a landing como um problema de contrato entre UI e conteúdo. A revisão vai:

1. Normalizar o conteúdo necessário no locale para `pt-BR` e `en-US`.
2. Ajustar os componentes da landing para consumir o formato real dos dados de forma robusta.
3. Atualizar a copy da seção de integrações para refletir status real do produto, removendo o falso "em breve".
4. Cobrir com testes os pontos que hoje quebram silenciosamente, especialmente pricing, integrações e chaves críticas de showcase/how-it-works.

## Content Direction

- Pricing deve ter nome, descrição, benefícios e CTA claros por plano.
- Integrações devem comunicar disponibilidade real:
  - Hevy: conexão/sincronização disponível.
  - MyFitnessPal: importação disponível.
  - Zepp Life: importação disponível.
- Showcase e conversas devem ter texto completo no locale, sem fallback para chave literal.
- Footer deve usar i18n também para links institucionais básicos.

## Constraints

- Preservar a estrutura visual geral da landing atual.
- Não introduzir refatoração ampla de layout.
- Seguir TDD para os bugs principais antes da implementação.
- Validar ao final com testes relevantes da landing, `npm run lint` e `npm run typecheck` em `frontend/`.

## Files Expected To Change

- `frontend/src/features/landing/components/Pricing.tsx`
- `frontend/src/features/landing/components/IntegrationLogos.tsx`
- `frontend/src/features/landing/components/HowItWorks.tsx`
- `frontend/src/features/landing/components/TrainerShowcase.tsx`
- `frontend/src/features/landing/components/ChatCarousel.tsx`
- `frontend/src/features/landing/components/ProductShowcase.tsx`
- `frontend/src/features/landing/components/Footer.tsx`
- `frontend/src/locales/pt-BR.json`
- `frontend/src/locales/en-US.json`
- Landing tests covering these components

## Testing Strategy

- Adicionar testes que falhem com o estado atual para:
  - CTA textual dos cards de pricing.
  - Status real das integrações, sem "Em breve".
  - Renderização de passos do `HowItWorks`.
  - Textos críticos do `ProductShowcase` e footer.
- Depois implementar a menor correção necessária para fazer os testes passarem.
