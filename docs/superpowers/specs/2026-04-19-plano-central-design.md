# Design: Plano Central no FityQ

## Resumo

Este documento define o conceito de `plano` como nova entidade central do produto FityQ. O plano deixa de ser apenas uma visualizacao agregada de treino, nutricao e peso e passa a ser a fonte principal da estrategia de acompanhamento do usuario. A IA cria, conduz, revisa e propõe ajustes no plano com aprovacao explicita do usuario.

O objetivo do recurso e transformar o app em um hub unico e premium de acompanhamento, no qual o usuario entende:

- qual e o plano atual
- o que precisa fazer hoje
- o que vem nos proximos dias
- como a IA esta interpretando sua evolucao
- quando e por que o plano precisa ser ajustado

## Objetivos do Produto

- Criar um objeto unico de alto valor percebido: `meu plano`
- Fazer a IA operar com contexto persistente do plano em toda conversa
- Tornar treino e nutricao uma execucao do plano, e nao fluxos isolados
- Criar uma experiencia premium de acompanhamento, com checkpoints e justificativas claras
- Manter o usuario no controle por meio de aprovacao explicita para mudancas materiais

## Fora de Escopo para a V1

- Edicao manual livre do plano pelo usuario
- Multiplos planos ativos por usuario
- Motor avancado de scoring de aderencia com peso sofisticado por categoria
- Timeline complexa com fases e semanas como objetos principais da UX
- Edicao administrativa completa do plano pelo painel admin

## Principios do Recurso

- Existe apenas `1 plano ativo por usuario`
- O plano tem `inicio` e `fim` explicitos
- O plano pode ser prorrogado ou reformulado pela IA com permissao do usuario
- O plano possui `checkpoints` visiveis e compreensiveis
- A IA nunca altera o plano silenciosamente
- O chat sempre opera com o `snapshot do plano vigente`
- O plano precisa parecer premium, mas tambem util no uso diario

## Experiencia Desejada

### Sensacao do produto

Dominante:

- elite / acompanhamento premium

Secundaria:

- cuidado e personalizacao

### Modelo mental do usuario

O usuario nao deve sentir que esta navegando entre modulos desconectados. O modelo mental passa a ser:

- eu tenho um plano ativo
- esse plano me diz o que fazer hoje
- a IA acompanha minha execucao
- a IA percebe quando algo nao esta funcionando
- qualquer mudanca importante e conversada comigo

## Abordagens Consideradas

### 1. Plano-orquestrador

O plano vira a entidade principal do dominio. Treino, nutricao, peso e checkpoints passam a servir de execucao, evidencia e acompanhamento do plano.

Pros:

- cria diferenciacao real no produto
- gera contexto forte para o prompt
- unifica UX e narrativa do coaching

Contras:

- exige modelagem propria
- requer versionamento e governanca claros

### 2. Plano-overlay

O plano seria apenas uma camada visual por cima dos dados ja existentes.

Pros:

- menor custo inicial

Contras:

- risco alto de parecer superficial
- IA continuaria operando em torno de dominios separados

### 3. Plano-prescricao

O plano seria um documento operacional forte, mas sem governar de fato a estrategia persistida.

Pros:

- UX inicial boa

Contras:

- ainda insuficiente como fonte de verdade

### Decisao

Adotar a abordagem `plano-orquestrador`, com entrega incremental:

- v1: plano ativo, missao de hoje, proximos dias, checkpoints, proposta de ajuste com aprovacao
- v2: aderencia mais rica, historico evolutivo mais profundo, explicacoes melhores da IA

## Estrutura do Plano

O plano e exibido ao usuario como um objeto unico. Internamente, ele pode ter divisao temporal e checkpoints, mas isso nao deve virar uma arvore de navegacao complexa.

### Campos conceituais

#### Identidade

- `id`
- `user_email`
- `status`
- `title`
- `objective_summary`
- `start_date`
- `end_date`
- `version`
- `previous_version_id`

#### Estrategia

- `primary_goal`
- `success_criteria`
- `constraints`
- `coaching_rationale`
- `adaptation_policy`

#### Execucao atual

- `today_training`
- `today_nutrition`
- `upcoming_days`
- `active_focus`
- `current_risks`
- `pending_changes`

#### Acompanhamento

- `checkpoints[]`
- `adherence_snapshot`
- `progress_snapshot`
- `last_ai_assessment`
- `last_user_acknowledgement`

#### Governanca

- `change_reason`
- `approval_request`
- `approved_at`
- `declined_at`
- `completed_at`

## Estados do Plano

Estados minimos recomendados:

- `draft`
- `awaiting_approval`
- `active`
- `adjustment_pending_approval`
- `completed`
- `archived`

### Regras

- `draft`: plano ainda sendo estruturado pela IA
- `awaiting_approval`: proposta inicial pronta e aguardando aprovacao
- `active`: plano vigente em uso
- `adjustment_pending_approval`: IA propôs mudanca material e aguarda resposta
- `completed`: plano encerrado com checkpoint final
- `archived`: plano historico, sem efeito operacional

## Fluxo de Vida do Plano

### 1. Criacao

- usuario conversa com a IA
- IA esclarece objetivo, restricoes, rotina e preferencias
- se o objetivo estiver difuso, a IA pode ajudar a defini-lo proativamente
- quando houver confianca suficiente, a IA gera uma proposta inicial
- a proposta e salva como `awaiting_approval`

### 2. Aprovacao inicial

- o usuario aprova no chat ou por CTA na tela do plano
- apenas apos aprovacao o plano passa a `active`
- enquanto a proposta nao for aprovada, o plano vigente anterior continua valendo

### 3. Execucao diaria

Com o plano ativo, o app passa a mostrar:

- resumo do plano
- missao de hoje
- proximos dias
- ultimo checkpoint
- estado atual do plano

### 4. Deteccao de necessidade de ajuste

A IA pode detectar necessidade de ajuste por:

- conversa com o usuario
- mudanca de objetivo ou rotina
- sinais de baixa aderencia
- sinais de que a estrategia nao esta funcionando

A decisao operacional e: a IA so ajusta quando julgar necessario, mediada pelo chat.

### 5. Proposta de ajuste

- a IA explica por que o plano precisa mudar
- pede permissao ao usuario
- registra proposta de ajuste em `adjustment_pending_approval`

### 6. Ajuste aprovado

- ao receber permissao, o backend cria nova versao do plano
- a versao anterior vira historico
- a nova versao passa a ser `active`
- o snapshot do prompt passa a usar a nova versao

### 7. Checkpoint

Cada checkpoint e um ritual premium de acompanhamento composto por:

- resumo executivo
- analise da IA
- decisao
- proxima etapa

### 8. Encerramento ou renovacao

Quando o plano atinge o fim:

- a IA realiza checkpoint final
- propoe encerramento, prorrogacao ou novo plano

## Governanca de Mudancas

### Regra principal

So a IA pode alterar o plano, e toda mudanca material exige permissao explicita do usuario.

### Mudancas materiais

Devem exigir aprovacao:

- alteracao de objetivo
- alteracao relevante de treino
- alteracao relevante de estrategia nutricional
- mudanca de datas do plano
- redefinicao de checkpoints
- reformulacao estrutural do plano

### Mudancas sem aprovacao

Nao devem existir na V1 se alterarem o significado operacional do plano. O produto deve ser conservador: se ha duvida, pedir permissao.

## Arquitetura Recomendada

### Backend

Criar `plan` como agregado proprio de dominio, separado de `user_profile`.

Justificativa:

- evita inflar `user_profile`
- facilita versionamento
- facilita historico e auditoria
- isola responsabilidades

### Prompt

O prompt nao deve receber o plano bruto inteiro. O backend deve gerar um `plan_prompt_snapshot` compacto e estavel, contendo:

- objetivo atual
- datas
- status
- foco atual
- missao de hoje
- proximos dias
- ultimo checkpoint
- restricoes criticas
- ajustes pendentes

Esse snapshot deve ser sempre injetado no prompt da IA, da mesma forma que hoje entram perfil, agenda e historico.

### Tools para a IA

Tools dedicadas recomendadas:

- `get_active_plan`
- `get_plan_prompt_snapshot`
- `create_plan_proposal`
- `propose_plan_adjustment`
- `approve_plan_change`
- `get_plan_checkpoints`
- `create_plan_checkpoint`
- `get_today_plan_brief`

Observacao: a V1 nao inclui tools de edicao manual pelo usuario.

### Integracao com dominios existentes

Treino, nutricao e peso permanecem como dominios separados, mas passam a ser interpretados como execucao e evidencia do plano:

- logs de treino ajudam a medir execucao do treino proposto
- logs de nutricao ajudam a medir alinhamento com a estrategia nutricional
- peso e composicao ajudam a avaliar resposta do plano

## Estrategia de UX

### Home do plano

Hierarquia aprovada: `Mission First`

#### 1. Hero do plano

Exibir:

- objetivo
- status
- datas
- versao
- CTA para conversar com a IA
- indicacao se ha ajuste aguardando aprovacao

#### 2. Missao de hoje

Bloco principal da tela com 3 cartoes:

- treino
- nutricao
- acompanhamento IA

#### 3. Proximos dias

Visao operacional de 3 a 7 dias para dar previsibilidade ao usuario.

#### 4. Ultimo checkpoint

Resumo da ultima leitura premium da IA.

#### 5. Estado do plano

Indicador resumido:

- on track
- atencao
- revisao sugerida
- aguardando aprovacao

#### 6. Ajustar plano

Permitir:

- chat livre como fluxo principal
- atalhos guiados como apoio

Atalhos sugeridos:

- treino pesado demais
- rotina mudou
- nao gostei
- quero acelerar
- quero reduzir carga

## Aderencia na V1

Manter aderencia simples e util:

- treino do dia: realizado / nao realizado / sem dado
- nutricao do dia: dentro / fora / sem dado
- checkpoint combina dados com contexto conversacional
- peso e composicao entram como sinal de resposta, nao como checklist diario

## Fluxo de Dados

### Criacao

- chat coleta contexto
- IA gera proposta
- backend persiste proposta
- frontend renderiza estado pendente
- usuario aprova
- backend ativa o plano

### Conversa diaria

- frontend carrega plano ativo
- backend inclui `plan_prompt_snapshot` em toda conversa
- IA responde sempre em cima do plano vigente

### Ajuste

- IA detecta necessidade
- IA pede permissao
- backend registra proposta
- usuario aprova
- backend cria nova versao ativa

### Checkpoint

- backend registra resumo, analise, decisao e proxima etapa
- frontend mostra a versao legivel do checkpoint

## Regras Criticas de Consistencia

- a IA nunca deve afirmar que o plano mudou antes da mudanca ter sido persistida
- se existe proposta pendente, ela nao substitui o plano vigente ate a aprovacao
- o prompt sempre deve usar a versao vigente, salvo em contextos explicitos de revisao da proposta
- historico de versoes deve ser preservado para auditoria e clareza

## Tratamento de Erros e Estados Vazios

### Sem plano ativo

- mostrar onboarding guiado do plano
- CTA principal: criar plano pelo chat

### Proposta pendente

- estado claro de `aguardando sua aprovacao`

### Plano expirado

- mostrar `revisao necessaria`
- manter visivel o plano anterior ate nova aprovacao

### Dados insuficientes

- IA pode operar com baixa confianca
- a interface deve deixar essa confianca explicita

### Divergencia entre plano e execucao real

- nao tratar como erro tecnico
- tratar como sinal de aderencia, contexto ou necessidade de ajuste

## Testes Recomendados

### Backend

- criacao de proposta inicial
- aprovacao de proposta
- bloqueio de mudanca sem aprovacao
- geracao correta do `plan_prompt_snapshot`
- criacao de nova versao em ajuste aprovado
- consistencia entre plano vigente e proposta pendente
- criacao e leitura de checkpoints

### Frontend

- renderizacao da home do plano sem plano
- renderizacao com proposta aguardando aprovacao
- renderizacao com plano ativo
- renderizacao com ajuste pendente
- renderizacao com plano expirado
- renderizacao dos 3 cartoes da missao de hoje
- exibicao correta do checkpoint e do estado do plano

### Integracao

- fluxo chat -> proposta inicial -> aprovacao -> plano ativo
- fluxo chat -> proposta de ajuste -> aprovacao -> nova versao ativa
- injecao do snapshot no prompt em conversas normais

## Rollout Recomendado

### V1

- entidade `plan`
- snapshot no prompt
- home do plano
- proposta inicial via chat
- aprovacao
- ajuste com permissao
- checkpoints basicos

### V2

- aderencia mais rica
- timeline de versoes
- explicacoes mais profundas da IA sobre decisoes
- visualizacoes historicas premium do plano

## Decisoes Fechadas Nesta Especificacao

- plano e entidade central do produto
- existe 1 plano ativo por usuario
- o plano tem inicio e fim explicitos
- a IA pode propor prorrogacao ou reorganizacao
- o plano sempre vai no prompt por meio de snapshot compacto
- so a IA altera o plano
- mudancas materiais exigem aprovacao do usuario
- a home segue hierarquia `Mission First`
- o bloco principal e `Missao de hoje`
- checkpoints sao rituais premium de acompanhamento

