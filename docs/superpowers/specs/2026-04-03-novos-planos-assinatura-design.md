# Novos Planos de Assinatura Design

## Goal

Redesenhar o catálogo de assinatura da FityQ para operar com três planos (`Free`, `Basic`, `Pro`), remover `Premium` das superfícies ativas e alinhar produto, pricing, onboarding e enforcement técnico com a proposta comercial desejada: trial com valor real, uso individual sem automações e plano completo com integrações.

## Current Findings

- O backend define hoje quatro planos em `backend/src/core/subscription.py`: `Free`, `Basic`, `Pro` e `Premium`.
- As regras atuais confirmadas no código são:
  - `Free`: `20` mensagens por dia, validade de `7` dias, somente trainer `gymbro`.
  - `Basic`: `100` mensagens por ciclo mensal.
  - `Pro`: `300` mensagens por ciclo mensal.
  - `Premium`: `1000` mensagens por ciclo mensal.
  - Fotos no chat só são permitidas para `Pro` e `Premium`.
- A landing page, a tela de assinatura em configurações e o onboarding usam implementações separadas para pricing/planos.
- O onboarding já permite escolher plano e já bloqueia trainers fora do `Free`, mas ainda expõe `Premium`.
- As integrações e importações aparecem na UI sem gate explícito por plano e o backend hoje não bloqueia, por assinatura, `Hevy`, `Telegram` ou importações de `MyFitnessPal`/`Zepp`.
- O fluxo Stripe ainda conhece `Premium` via `STRIPE_PRICE_ID_PREMIUM` e pelo mapeamento atual do webhook.

## Product Direction

O catálogo deve vender três estágios de maturidade do usuário:

- `Free`: provar valor rápido e fazer o usuário sentir a qualidade do coaching.
- `Basic`: vender acompanhamento pessoal para uso manual, sem automações.
- `Pro`: vender conveniência, consistência e operação com dados reais por meio de fotos, integrações e importações.

Essa divisão é importante porque preço sozinho converte pior do que um salto claro de capacidade. O `Basic` não deve ser comunicado como um plano capado, e sim como o plano focado no essencial. O `Pro` deve concentrar os gatilhos de upgrade ligados a conveniência e aderência.

## Plan Catalog

### Free

Objetivo comercial: trial com valor real, sem automações.

Capacidades:

- `20` mensagens por dia.
- validade de `7` dias.
- apenas trainer `gymbro`.
- sem fotos no chat.
- sem integrações.
- sem Telegram.
- sem importações.

### Basic

Objetivo comercial: uso individual manual, com todos os trainers, mas sem automações.

Capacidades:

- `100` mensagens por ciclo mensal.
- todos os trainers liberados.
- sem fotos no chat.
- sem integrações.
- sem Telegram.
- sem importações.

### Pro

Objetivo comercial: produto completo, com automação e dados externos.

Capacidades:

- `300` mensagens por ciclo mensal.
- todos os trainers liberados.
- fotos liberadas no chat.
- integrações liberadas.
- Telegram liberado.
- importações liberadas.

## Capability Model

As regras de plano devem deixar de existir de forma implícita ou espalhada. A implementação deve centralizar um catálogo de capacidades por plano para servir como fonte única de verdade.

Esse catálogo deve contemplar, no mínimo:

- `monthly_limit`
- `daily_limit`
- `validity_days`
- `allowed_trainers`
- `image_input_enabled`
- `integrations_enabled`
- `telegram_enabled`
- `imports_enabled`
- `price`
- `marketing badge/copy metadata` quando fizer sentido para o frontend

`integrations_enabled` cobre as integrações já suportadas hoje e quaisquer integrações equivalentes futuras expostas na aba de integrações. Para o escopo atual, isso inclui `Hevy`, `MyFitnessPal`, `Zepp` e recursos da mesma família. `telegram_enabled` fica separado porque há endpoint e UX próprios e porque a copy do produto o destaca como benefício distinto.

## Enforcement Rules

As regras não podem ficar só na UI. O backend deve ser a camada de autoridade.

### Backend

O backend deve bloquear por plano:

- upload de imagens no chat fora do `Pro`;
- endpoints de `Hevy` fora do `Pro`;
- endpoints de `Telegram` fora do `Pro`;
- importações de `MyFitnessPal` e `Zepp` fora do `Pro`;
- seleção e persistência de trainers fora do conjunto permitido pelo plano.

Quando houver bloqueio, o backend deve responder com erro explícito de autorização/capacidade, não com falha genérica.

### Frontend

O frontend deve refletir as capacidades do plano e evitar fluxos inválidos:

- esconder ou desabilitar ações não permitidas;
- mostrar motivo do bloqueio com copy de upgrade;
- impedir seleção de recursos indisponíveis no onboarding;
- manter o estado da UI coerente com o plano atual em configurações e landing.

## Surfaces Affected

### Landing Page

A landing deve mostrar apenas `Free`, `Basic` e `Pro`. O card de plano precisa reforçar o salto de valor entre manual e automatizado.

Regras:

- destacar visualmente o `Pro` como plano recomendado;
- remover qualquer menção a `Premium`;
- usar bullets que expressem capacidade real, não promessas vagas.

### Settings > Assinatura

A aba de assinatura deve usar o mesmo componente base de exibição dos planos usado na landing e no onboarding, mudando apenas comportamento e CTA.

Regras:

- exibir plano atual;
- permitir upgrade/downgrade entre os três planos suportados;
- remover `Premium`;
- manter ação de gerenciamento Stripe para planos pagos.

### Onboarding

O onboarding deve usar o mesmo componente base de plano e refletir claramente as capacidades e limitações.

Regras:

- remover `Premium`;
- explicar que `Free` é trial;
- deixar claro que fotos, integrações, Telegram e importações só existem no `Pro`;
- impedir seleção de recursos incompatíveis com o plano escolhido;
- preservar o bloqueio de trainer por plano.

### Settings > Integrações

A aba de integrações precisa deixar de assumir disponibilidade universal.

Regras:

- para `Free` e `Basic`, renderizar estado bloqueado com mensagem do tipo “Disponível no Pro”;
- para `Pro`, manter a experiência atual de conexão/uso;
- imports devem seguir a mesma regra das integrações.

### Chat / Perfil

As superfícies que aceitam foto ou refletem benefícios do plano precisam seguir o novo catálogo.

Regras:

- foto de perfil não é escopo desta mudança;
- fotos no chat continuam sendo um benefício de plano e devem ficar exclusivas do `Pro`;
- qualquer affordance de envio de imagem fora do `Pro` deve ser removida ou desabilitada com explicação.

## Shared Plan Component

O frontend deve ter um único componente base para cards de plano, reutilizável em:

- landing page;
- configurações > assinatura;
- onboarding.

O componente deve aceitar variações leves de contexto, por exemplo:

- `marketing`: CTA comercial e destaque visual;
- `selection`: estado selecionado para onboarding;
- `management`: plano atual, mudança de plano e loading de ação.

O conteúdo exibido deve vir de uma estrutura compartilhada, para evitar divergência entre textos, preços, features e badges em cada tela.

## Copy Direction

O posicionamento comercial deve ser:

- `Free`: “Experimente”
- `Basic`: “Seu treinador pessoal no dia a dia”
- `Pro`: “Tudo conectado para executar melhor”

Exemplos de copy:

### Free

- título: `Experimente`
- subtítulo: `Teste o coaching da FityQ por 7 dias.`
- bullets:
  - `20 mensagens por dia`
  - `1 treinador`
  - `Sem integrações`
  - `Sem fotos`

### Basic

- título: `Basic`
- subtítulo: `Seu treinador pessoal no dia a dia, sem automações.`
- bullets:
  - `100 mensagens por mês`
  - `Todos os treinadores`
  - `Uso manual e focado`
  - `Sem integrações e sem fotos`

### Pro

- título: `Pro`
- subtítulo: `A experiência completa com dados, fotos e automações.`
- bullets:
  - `300 mensagens por mês`
  - `Fotos no chat`
  - `Hevy, Telegram e importações`
  - `Todos os treinadores`

Toda copy nova ou alterada deve ser traduzida em `pt-BR`, `en-US` e `es-ES`.

## Stripe Scope

O catálogo exposto ao usuário deve ter só `Free`, `Basic` e `Pro`.

Regras:

- remover `Premium` das estruturas de pricing no frontend;
- remover `Premium` do mapeamento exibido em pricing, onboarding e assinatura;
- ajustar o mapeamento Stripe para operar apenas com os planos mantidos;
- o tratamento de migração de usuários legados `Premium` está explicitamente fora de escopo desta mudança.

## Out of Scope

- migração de usuários existentes entre planos;
- redefinição de preços monetários, desde que `Basic` e `Pro` mantenham preços atuais ou equivalente decidido depois;
- criação de novas integrações além das já existentes no produto;
- mudança no comportamento de foto de perfil em configurações;
- refatoração ampla de layout fora das telas de pricing/onboarding/assinatura/integrações.

## Files Expected To Change

- `backend/src/core/subscription.py`
- `backend/src/api/endpoints/message.py`
- `backend/src/api/endpoints/trainer.py`
- `backend/src/api/endpoints/hevy.py`
- `backend/src/api/endpoints/telegram.py`
- `backend/src/api/endpoints/nutrition.py`
- `backend/src/api/endpoints/stripe.py`
- modelos e testes relacionados a planos, onboarding e limites no backend
- `frontend/src/features/landing/components/Pricing.tsx`
- `frontend/src/features/settings/components/SubscriptionView.tsx`
- `frontend/src/features/onboarding/components/OnboardingView.tsx`
- `frontend/src/features/settings/components/IntegrationsView.tsx`
- um novo componente compartilhado de plano em `frontend/src/shared` ou área equivalente
- `frontend/src/shared/constants/stripe.ts`
- arquivos de locale `pt-BR`, `en-US` e `es-ES`
- testes de frontend e backend cobrindo gating por plano e a UI de pricing

## Testing Strategy

Seguir TDD para cada mudança de regra importante.

Cobertura mínima esperada:

- testes unitários do catálogo de planos e capacidades;
- testes unitários/integrados de bloqueio de trainer por plano;
- testes unitários/integrados de bloqueio de imagem fora do `Pro`;
- testes unitários/integrados de bloqueio de `Hevy`, `Telegram` e importações fora do `Pro`;
- testes de frontend para garantir:
  - ausência de `Premium`;
  - renderização consistente do mesmo conjunto de planos em landing, onboarding e assinatura;
  - mensagens de bloqueio corretas em integrações;
  - seleção e CTA corretos por contexto;
- validação final obrigatória:
  - `cd frontend && npm run lint && npm run typecheck`
  - `cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src`

## Risks

- Regras de plano espalhadas entre backend, onboarding, landing e settings podem gerar inconsistência se a centralização for parcial.
- O componente compartilhado pode ser acoplado demais ao contexto de uma tela específica se não houver separação clara entre dados e comportamento.
- Se o backend não bloquear integrações/importações, a UI sozinha não garante a política comercial.
- A retirada de `Premium` pode deixar referências residuais em testes, locales, scripts ou mapeamentos Stripe.

## Success Criteria

- O produto passa a expor apenas `Free`, `Basic` e `Pro` nas superfícies ativas.
- Landing, onboarding e configurações usam o mesmo componente base para exibição de planos.
- `Free` e `Basic` não conseguem usar fotos, integrações, Telegram ou importações.
- `Pro` mantém acesso completo aos recursos avançados existentes.
- O posicionamento comercial fica coerente com a capacidade real do produto.
