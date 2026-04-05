# Stripe Hybrid Test Automation Design

## Goal

Garantir alta confiança na funcionalidade core de billing da FityQ com uma estratégia híbrida de testes:

- `stripe-mock` para contratos rápidos e smoke tests
- Stripe real em `test mode` para lifecycle real de assinaturas
- Playwright e integração backend validando o comportamento do app ponta a ponta

## Problem

Hoje o repositório já sobe `stripe-mock` no ambiente containerizado, mas isso não é suficiente para provar os cenários de assinatura que importam de verdade:

- criação real de subscription
- cancelamento imediato
- cancelamento no fim do período
- mudança de preço/plano
- falha de pagamento e transição para `past_due` / `unpaid`
- reativação
- renovação de ciclo e reset de contadores
- ordem real e repetição de webhooks

`stripe-mock` cobre bem a superfície da API, mas não substitui o motor real de billing do Stripe.

## Decision

Adotar uma arquitetura de testes híbrida com três camadas.

### Layer 1: Unit + Contract Tests

Objetivo:

- validar regras internas do app com feedback rápido
- manter testes determinísticos e baratos

Responsabilidade:

- parsing de webhook
- mapeamento de `price_id`
- resets de contadores
- downgrade para `Free`
- fallback de trainer
- idempotência de handlers
- invariantes locais do domínio

Infra:

- `stripe-mock` e payloads controlados

### Layer 2: Integration Tests Against Stripe Test Mode

Objetivo:

- validar o lifecycle real do billing
- provar que o backend reage corretamente aos objetos reais do Stripe

Responsabilidade:

- criar customer, checkout session e subscription reais
- trocar price/assinatura
- cancelar
- simular inadimplência e eventos de cobrança
- validar que o perfil local converge para o estado esperado

Infra:

- Stripe real em `test mode`
- Stripe CLI para forwarding e trigger de eventos, quando necessário
- test harness próprio no repositório

### Layer 3: End-to-End App + Stripe

Objetivo:

- validar a jornada do usuário no app com estado de billing real

Responsabilidade:

- CTA -> checkout
- retorno para app
- portal de billing
- reflexo do estado na UI
- perda de entitlement e bloqueios de produto

Infra:

- Playwright
- backend e frontend containerizados
- Stripe test mode
- harness compartilhado com a camada de integração

## Recommendation

O CI e a rotina de dev devem tratar cada camada de forma diferente:

- PR padrão:
  - unit/contract Stripe com `stripe-mock`
  - subset pequeno de integração real
- nightly / branch protegida / release gate:
  - suíte completa de integração real
  - suíte e2e Stripe crítica

Isso reduz tempo e custo sem sacrificar confiança.

## Test Harness Design

Será criado um harness de testes Stripe com responsabilidades explícitas:

- provisionar recursos efêmeros no Stripe test mode
- gerar IDs únicos por teste para correlação
- criar e atualizar subscriptions reais
- acionar eventos suportados via Stripe CLI quando necessário
- esperar convergência do backend local com polling e timeouts explícitos
- limpar customers/subscriptions após cada teste

Helpers de alto nível esperados:

- `create_checkout_session_for_test_user`
- `create_direct_subscription_for_test_user`
- `swap_subscription_price`
- `cancel_subscription_immediately`
- `cancel_subscription_at_period_end`
- `reactivate_subscription`
- `trigger_invoice_payment_failure`
- `await_user_profile_state`
- `cleanup_test_customer`

## Scenario Matrix

Os cenários obrigatórios para cobertura automatizada são:

- nova assinatura Pro
- assinatura criada com fallback por metadata/email
- checkout concluído com webhook recebido
- alteração de assinatura/preço
- cancelamento imediato
- cancelamento no fim do período
- reativação antes do fim do período
- renovação de ciclo com reset de mensagens e fotos
- `past_due`
- `unpaid` ou estado equivalente suportado pela conta/test mode
- downgrade para `Free`
- bloqueio de chat/imagem/Telegram/imports após perda de entitlement
- reset do trainer para `gymbro`
- duplicidade de webhook
- webhooks fora de ordem não corrompem estado final

## CI Strategy

### Fast Path

Rodar em PR:

- unit tests existentes de webhook
- novos integration tests curtos marcados como `stripe_live_smoke`

### Full Billing Path

Rodar em gate mais forte:

- todos os `stripe_live`
- Playwright Stripe crítico

### Secrets

Necessário configurar:

- `STRIPE_TEST_SECRET_KEY`
- `STRIPE_TEST_WEBHOOK_SECRET`
- `STRIPE_CLI_API_KEY` ou autenticação equivalente do Stripe CLI

Esses segredos não devem ser exigidos para a suíte local default. A suite live deve falhar com mensagem clara ou ser explicitamente opt-in quando os segredos não estiverem presentes.

## Reliability Rules

Para a suíte ser confiável:

- nenhum teste pode depender de estado pré-existente no Stripe
- todo teste precisa criar seus próprios recursos
- cleanup precisa ser idempotente
- timeouts precisam ser explícitos e curtos
- correlação deve usar metadata única por teste
- assertions devem validar estado no Stripe e no app

## Risks

### Network Flakiness

Mitigação:

- separar smoke e full suite
- usar retries apenas em operações de espera por convergência, não em assertions de negócio

### Stripe Test Mode Limitations

Nem todo cenário financeiro avançado é perfeitamente reproduzível apenas com trigger artificial.

Mitigação:

- mapear o que vem de API direta, o que vem de Stripe CLI, e o que depende de Test Clocks

### Slow End-to-End Runs

Mitigação:

- manter e2e Stripe enxuto
- deixar exaustão de estados na camada de integração backend

## Affected Areas

- `backend/tests`
- `frontend/e2e`
- `docker-compose.test.yml` ou stack equivalente
- scripts de teste/CI
- documentação operacional do projeto

## Success Criteria

Consideraremos essa iniciativa bem-sucedida quando:

- os estados críticos de assinatura estiverem cobertos automaticamente
- os testes distinguirem claramente `mock` vs `live`
- o time conseguir rodar localmente os fluxos críticos
- o CI tiver um gate confiável para regressões de billing
