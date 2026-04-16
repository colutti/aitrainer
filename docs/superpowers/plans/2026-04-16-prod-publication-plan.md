# FityQ Production Publication Plan

> **Objetivo:** publicar a última versão do produto em produção com segurança, cobrindo autenticação Firebase, billing Stripe, mudanças de ambiente, fluxo de deploy e um feature toggle para manter cadastro e compra temporariamente desativados durante a validação.

## 1. Estado Atual Verificado

### Produção atual

- Projeto Firebase ativo: `fityq-488619`
- Região Cloud Run: `europe-southwest1`
- Serviços ativos:
  - `aitrainer-backend`
  - `aitrainer-backend-admin`
  - `aitrainer-frontend`
  - `aitrainer-frontend-admin`
- Todos os serviços estão servindo `100%` do tráfego na revisão `00008` atual.
- O frontend público em produção continua apontando para `aitrainer-backend` via `BACKEND_URL`.
- O Firebase Hosting está configurado para reescrever para o serviço `aitrainer-frontend`.

### Gap entre PROD e o código atual

O `main` local está muito à frente do ambiente publicado e inclui, no mínimo:

- autenticação com Firebase no lugar do login clássico;
- fluxo público de onboarding e novo cadastro;
- cobrança com Stripe, checkout, portal e webhooks;
- novo catálogo de planos (`Free`, `Basic`, `Pro`);
- landing page nova, com foco em conversão;
- mudanças operacionais em compose, verificação e CI.

### Fato importante sobre a produção atual

O backend hoje em produção **não** está configurado com as novas variáveis obrigatórias de Firebase Auth e Stripe. O frontend atual em produção também **não** está parametrizado com as variáveis do Firebase exigidas pelo código atual.

Isso significa que **não é seguro subir a última versão direto** sem antes ajustar build/deploy e variáveis de ambiente.

## 2. Blockers Obrigatórios Antes de Subir a Última Versão

### 2.1 Firebase no frontend

O código atual do frontend depende de:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

Problema:

- o `frontend/Dockerfile` hoje só expõe `VITE_API_URL` como build arg;
- as variáveis `VITE_*` do Firebase são consumidas em build time pelo Vite;
- o Cloud Run do frontend hoje só recebe `BACKEND_URL` em runtime.

Conclusão:

- antes do deploy da última versão, o pipeline de build do frontend precisa aceitar e injetar as variáveis do Firebase em build time, ou o frontend publicado vai quebrar a autenticação.

### 2.2 Firebase no backend

O backend atual exige:

- `FIREBASE_CREDENTIALS`

Sem essa variável:

- o Firebase Admin não inicializa;
- login via Firebase não funciona corretamente;
- o script de migração de usuários para Firebase não pode rodar em produção.

### 2.3 Stripe no backend

O backend atual exige para operação real de billing:

- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_BASIC`
- `STRIPE_PRICE_ID_PRO`

Observações:

- `STRIPE_API_BASE` pode continuar no default da API real do Stripe;
- `STRIPE_PRICE_ID_PREMIUM` ainda existe em config, mas o produto atual está orientado a `Free`, `Basic` e `Pro`;
- a produção atual não expõe essas variáveis.

### 2.4 IDs do Stripe no frontend

Hoje o frontend usa IDs de preço hardcoded em:

- `frontend/src/shared/constants/stripe.ts`

Isso é um risco de release porque:

- o backend reconhece preços por variável de ambiente;
- o frontend usa IDs fixos do repositório;
- qualquer divergência entre código e Stripe de produção quebra checkout ou cria cobrança no preço errado.

Conclusão:

- antes de publicar, é preciso confirmar que esses IDs correspondem exatamente ao Stripe de produção, ou corrigir a origem desses IDs.

## 3. Toggle Temporário Obrigatório Antes da Abertura Pública

### Objetivo

Publicar a última versão em produção, mas manter temporariamente:

- cadastro de novos usuários desativado;
- compra de planos desativada.

### Regras do toggle

- nome sugerido: `ENABLE_NEW_USER_SIGNUPS`
- se a variável estiver ausente: default `False`
- se `False`: bloquear cadastro novo e compra nova
- se `True`: liberar cadastro novo e compra nova

### Onde o toggle precisa atuar

#### Backend, como camada autoritativa

- `backend/src/api/endpoints/user.py`
  - bloquear criação implícita de usuário novo em `/user/login`
  - bloquear alias `/user/social-login` para novos usuários
- `backend/src/api/endpoints/onboarding.py`
  - bloquear `/onboarding/profile` quando for fluxo de novo usuário ainda não consolidado
- `backend/src/api/endpoints/stripe.py`
  - bloquear `/stripe/create-checkout-session`
- `backend/src/core/config.py`
  - adicionar a variável com default seguro

#### Frontend, para UX coerente

- `frontend/src/features/auth/LoginPage.tsx`
  - esconder ou desabilitar registro quando o toggle estiver desligado
- `frontend/src/shared/hooks/useAuth.ts`
  - impedir tentativa de cadastro por fluxo direto
- `frontend/src/features/onboarding/components/OnboardingPage.tsx`
  - impedir tentativa de checkout no onboarding
- `frontend/src/features/settings/components/SubscriptionPage.tsx`
  - desabilitar contratação/upgrade enquanto o toggle estiver desligado
- `frontend/src/features/landing/components/Pricing.tsx`
  - desabilitar CTAs de assinatura

#### CTAs da landing que também precisam respeitar o toggle

- `frontend/src/features/landing/components/Hero.tsx`
- `frontend/src/features/landing/components/FinalCTA.tsx`
- `frontend/src/features/landing/components/StickyMobileCTA.tsx`
- `frontend/src/features/landing/components/TrainerShowcase.tsx`
- `frontend/src/features/landing/components/Pricing.tsx`

### Estratégia recomendada para o toggle

- backend como fonte única de verdade;
- frontend consumindo esse estado via endpoint público simples;
- backend sempre validando novamente, mesmo que a UI já esteja bloqueando.

## 4. Estratégia de Publicação Recomendada

## Fase 0: Congelar o release candidate

- Escolher um SHA exato para release, em vez de usar `main` mutável.
- Recomendação: cortar o release candidate a partir do `main` atual e só então validar/deployar.
- Registrar esse SHA no plano de execução e nos comandos de build.

## Fase 1: Entregar primeiro o kill switch de cadastro e compra

Objetivo:

- subir a última versão em produção sem abrir aquisição pública antes da validação.

Passos:

- implementar o toggle no backend e frontend;
- garantir default `False`;
- validar localmente:
  - landing com planos desabilitados;
  - página de assinatura do usuário logado bloqueada;
  - login de usuário existente continua funcionando;
  - novo cadastro falha;
  - checkout falha.

Resultado esperado:

- a versão mais nova pode ser publicada em PROD com feature freeze comercial.

## Fase 2: Preparar build e deploy para suportar a versão atual

Objetivo:

- fazer o processo de publicação aceitar as necessidades reais da codebase atual.

Passos:

- adaptar o build do frontend principal para aceitar as variáveis `VITE_FIREBASE_*` em build time;
- revisar se o admin frontend precisa de ajustes equivalentes;
- definir procedimento único de build/push/deploy para:
  - `backend`
  - `frontend`
  - `backend-admin`
  - `frontend-admin`
- abandonar o risco de depender apenas de `:latest`; preferir imagem tagueada com SHA do release.

Resultado esperado:

- existe um caminho repetível para subir a última versão completa.

## Fase 3: Provisionar e revisar configuração de produção

### Backend principal

Adicionar/revisar:

- `FIREBASE_CREDENTIALS`
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_BASIC`
- `STRIPE_PRICE_ID_PRO`
- `ENABLE_NEW_USER_SIGNUPS=false`

### Frontend principal

Injetar em build time:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

Valores reais já existem no projeto Firebase e podem ser extraídos do app web `fityq-web`.

### Stripe

- confirmar produtos e preços reais de `Basic` e `Pro`;
- confirmar que os IDs usados no frontend batem com o Stripe de produção;
- configurar webhook para o endpoint público novo do backend;
- confirmar billing portal habilitado.

## Fase 4: Migração de usuários legados para Firebase

Objetivo:

- preservar o acesso dos usuários existentes quando o login clássico deixar de ser a referência.

Artefato existente:

- `backend/scripts/migrate_users_to_firebase.py`

Comportamento atual do script:

- cria usuários no Firebase sem senha migrada;
- o usuário legado depois entra por:
  - Google, ou
  - fluxo de “esqueci minha senha”.

Passos recomendados:

- fazer backup/export dos usuários antes da migração;
- rodar dry run ou amostra controlada fora de PROD;
- rodar a migração em produção com `FIREBASE_CREDENTIALS` configurado;
- comunicar que:
  - a conta continua sendo o mesmo e-mail;
  - o usuário pode precisar usar redefinição de senha;
  - Google login deve consolidar a mesma conta.

Risco operacional:

- usuários antigos podem estranhar a mudança de auth se isso não for comunicado antes do deploy.

## Fase 5: Validação técnica antes do deploy

Rodar no release candidate:

- `make verify`
- `make verify-all` ou `make test-once`

Além da suíte automatizada, executar smoke validation focada em:

- login com usuário já existente;
- bloqueio de novo cadastro com toggle desligado;
- bloqueio de compra na landing com toggle desligado;
- bloqueio de compra em configurações com toggle desligado;
- onboarding público sem abertura de checkout;
- admin continua operacional;
- dashboard e navegação principal carregam normalmente.

## Fase 6: Subir a última versão para produção

Este passo precisa existir explicitamente no rollout.

Sequência recomendada:

1. buildar as quatro imagens a partir do SHA congelado do release candidate;
2. publicar as imagens no Artifact Registry com tag imutável;
3. deployar `aitrainer-backend`;
4. deployar `aitrainer-frontend` usando o backend novo e o build com Firebase configurado;
5. deployar `aitrainer-backend-admin`;
6. deployar `aitrainer-frontend-admin`;
7. confirmar se o Firebase Hosting continua reescrevendo para `aitrainer-frontend`;
8. confirmar health checks e revisão pronta em Cloud Run.

Observação:

- esse é o ponto em que a “última versão” realmente sobe para PROD;
- a recomendação é fazer isso **com o toggle desligado**.

## Fase 7: Smoke test em produção com toggle desligado

Depois do deploy:

- validar login de usuário legado;
- validar login social existente;
- validar que novo cadastro está bloqueado;
- validar que planos da landing não iniciam compra;
- validar que planos da área logada não iniciam compra;
- validar que checkout do Stripe está bloqueado quando acionado manualmente;
- validar que o produto principal continua utilizável para usuários existentes.

Resultado esperado:

- a versão nova está em produção, mas sem abrir entrada comercial nova.

## Fase 8: Abrir gradualmente cadastro e compra

Quando a validação em PROD terminar:

- ativar `ENABLE_NEW_USER_SIGNUPS=true`;
- repetir smoke test de:
  - cadastro novo;
  - onboarding novo;
  - checkout de `Basic`;
  - checkout de `Pro`;
  - webhook de assinatura;
  - gestão de assinatura no portal.

## Fase 9: Plano de rollback

Se a publicação falhar:

- voltar os quatro serviços Cloud Run para a revisão anterior;
- manter `ENABLE_NEW_USER_SIGNUPS=false`;
- desabilitar webhook novo do Stripe se necessário;
- comunicar internamente que o rollout foi interrompido;
- reabrir somente após correção e nova validação.

## 5. Riscos Mais Importantes

### Risco 1: frontend novo sem Firebase configurado

Impacto:

- login e registro quebram imediatamente.

Mitigação:

- não publicar o frontend novo antes de resolver o build-time config.

### Risco 2: usuários legados sem caminho claro de acesso

Impacto:

- suporte e fricção na primeira entrada pós-migração.

Mitigação:

- migrar usuários antes;
- comunicar reset de senha e login Google.

### Risco 3: Stripe com IDs divergentes entre frontend e backend

Impacto:

- checkout falha ou cobra o preço errado.

Mitigação:

- reconciliar IDs de produção antes do deploy.

### Risco 4: publicar a landing nova sem o kill switch

Impacto:

- aquisição de usuários e tentativa de compra antes da validação operacional.

Mitigação:

- entregar e ativar o toggle antes da abertura pública.

## 6. Ordem Recomendada de Execução

1. Congelar o SHA da release.
2. Implementar o toggle de cadastro/compra com default desligado.
3. Ajustar pipeline/build do frontend para Firebase em build time.
4. Provisionar env vars de Firebase e Stripe em produção.
5. Preparar e executar migração de usuários para Firebase.
6. Rodar verificação completa no release candidate.
7. Subir a última versão para produção com o toggle desligado.
8. Executar smoke test em produção.
9. Só então habilitar cadastro e compra.

## 7. Decisões Que Ainda Precisam Ser Fechadas

- se os IDs de preço hardcoded do frontend serão mantidos ou removidos antes do release;
- se haverá comunicação formal aos usuários sobre a mudança para Firebase;
- se a abertura comercial será total de uma vez ou gradual após algumas horas/dias de observação em PROD.
