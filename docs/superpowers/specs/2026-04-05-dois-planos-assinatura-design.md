# Dois Planos de Assinatura Design

## Goal

Simplificar a FityQ para operar com apenas dois planos comerciais, `Grátis` e `Pro`, com um trial real de 7 dias do `Pro` para novos usuários, enforcement técnico consistente no backend, pricing promocional no frontend e Stripe configurado para preço cheio de `6.99` com oferta visível de `4.99`.

## Decisions Confirmed

- Catálogo final:
  - `Grátis`
  - `Pro`
- `Grátis` continua existindo indefinidamente.
- Todo novo usuário entra em `Grátis` com `7` dias de benefícios equivalentes ao `Pro`.
- Após o trial, o usuário continua em `Grátis` com restrições permanentes.
- O treinador fixo do `Grátis` é o treinador atual `gymbro`, tratado comercialmente como `Breno`.
- O `Pro` terá preço cheio de `6.99` e preço promocional exibido de `4.99`.
- O modelo padrão para todos os usuários será `gemini-2.5-flash-lite`.
- Os limites do `Pro` resetam pelo ciclo de cobrança do Stripe.

## Product Model

### Grátis

Durante os primeiros 7 dias:

- tem todos os benefícios do `Pro`
- usa o mesmo modelo `gemini-2.5-flash-lite`

Depois dos 7 dias:

- não pode mandar mensagens para o treinador
- não pode subir fotos no chat
- não pode trocar de treinador
- fica no `Breno` (`gymbro`)
- não pode usar Telegram
- não pode usar integrações
- não pode fazer importações
- pode continuar registrando dados manualmente

Registros manuais que devem continuar disponíveis:

- peso e composição corporal
- treino manual
- nutrição manual
- edição de perfil e metas
- visualização de histórico já registrado

### Pro

- pode usar tudo no sistema
- `500` mensagens por ciclo de cobrança
- `15` fotos por ciclo de cobrança
- todos os treinadores
- Telegram
- integrações
- importações
- preço cheio `6.99`
- preço promocional `4.99`

## Capability Model

O sistema deve parar de usar `subscription_plan` sozinho como fonte de verdade para tudo. O backend precisa representar:

- plano base do usuário: `Free` ou `Pro`
- trial ativo até data/hora específica
- capacidades efetivas calculadas em runtime
- contadores de mensagens por ciclo
- contadores de fotos por ciclo

Capacidades mínimas:

- `can_chat`
- `monthly_message_limit`
- `messages_used_this_cycle`
- `can_send_images`
- `monthly_photo_limit`
- `photos_used_this_cycle`
- `allowed_trainers`
- `can_use_telegram`
- `can_use_integrations`
- `can_use_imports`
- `is_trial_active`
- `trial_ends_at`

## Enforcement Rules

### Backend

O backend deve ser a autoridade final para:

- bloqueio de envio de mensagem após fim do trial no `Grátis`
- bloqueio de imagem fora de trial/`Pro`
- bloqueio de trainers fora de trial/`Pro`
- reset automático para `gymbro` em downgrade ou trial expirado
- bloqueio de Telegram fora de trial/`Pro`
- bloqueio de integrações/importações fora de trial/`Pro`
- contagem de mensagens por ciclo
- contagem de fotos por ciclo
- reset de contadores quando o Stripe abrir novo ciclo

### Frontend

O frontend deve apenas refletir e vender upgrade:

- esconder ou desabilitar ações não permitidas
- mostrar paywall contextual
- mostrar preço cheio riscado e preço promocional
- exibir claramente trial de 7 dias
- alinhar landing, onboarding e configurações com o mesmo catálogo

## Stripe Direction

O Stripe deve operar com:

- um único plano pago recorrente (`Pro`)
- um ou mais `price_id` por moeda para o preço promocional vigente
- possibilidade de manter metadados ou configuração para exibir:
  - preço cheio `6.99`
  - preço atual `4.99`

Questão importante: o Stripe Checkout trabalha com o preço real cobrado no `price_id`, não com “preço cheio cortado” apenas visual. Portanto, o efeito promocional exigirá uma destas estratégias:

1. `Price` promocional ativo e preço cheio exibido só no frontend.
2. `Coupon`/`Promotion Code` aplicado sobre um `Price` cheio.
3. Dois catálogos de preço por moeda com gestão explícita da campanha.

A recomendação é usar `price_id` promocional por moeda para simplificar a operação agora, mantendo o preço cheio apenas como referência de marketing no frontend.

## Pricing & Margin

Baseado no uso real recente do usuário local analisado:

- média de entrada por chat: `21,106` tokens
- média de saída por chat: `738` tokens
- modelo alvo: `gemini-2.5-flash-lite`

Estimativa para `500` chats/mês:

- custo de IA por usuário `Pro`: aproximadamente `US$ 1.20`
- receita bruta por usuário `Pro` a `US$ 4.99`: `US$ 4.99`
- margem bruta de IA aproximada: `US$ 3.79`

Com preço cheio de `US$ 6.99`, a margem bruta de IA sobe para aproximadamente `US$ 5.79`.

Essa conta não inclui:

- Stripe fees
- impostos
- infra
- embeddings
- custos indiretos operacionais

## Main Risks

### Produto

- o `Grátis` após 7 dias fica muito restrito; isso simplifica a oferta, mas pode reduzir retenção
- trial de 7 dias pode ser abusado com múltiplas contas

### Técnica

- hoje o código ainda carrega semântica antiga de `Basic`, `Pro`, `Premium` em múltiplos pontos
- o frontend ainda hardcode preços por locale
- não existe contador mensal explícito para fotos
- o trial atual está acoplado demais ao plano `Free`

### Comercial

- promoção de `4.99` precisa ficar coerente no Stripe, no checkout, no portal e nas telas
- moedas precisam ser tratadas por preço real do Stripe, não por string fixa no frontend

## Surfaces Affected

- backend subscription/capabilities
- webhook e checkout Stripe
- landing page
- onboarding
- settings > assinatura
- settings > trainer
- settings > integrações
- chat/paywalls
- admin users/editing
- traduções `pt-BR`, `en-US`, `es-ES`

## Migration Direction

- usuários `Basic` atuais devem migrar para `Pro`
- usuários `Pro` atuais devem migrar para o novo `Pro`
- usuários `Free` existentes continuam `Free`
- trial não deve ser concedido retroativamente para toda a base por padrão

## Recommended Implementation Shape

1. Separar `plano` de `trial`.
2. Consolidar enforcement no backend.
3. Expor capacidades efetivas para o frontend.
4. Remover `Basic` e `Premium` de todas as superfícies.
5. Trocar catálogo visual para `Grátis` + `Pro`.
6. Implementar preço promocional com preço cheio riscado no frontend.
7. Alinhar Stripe ao preço promocional e às moedas reais.
