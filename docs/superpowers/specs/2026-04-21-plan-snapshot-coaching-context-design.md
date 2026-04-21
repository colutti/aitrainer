# Design: Enriquecimento do PlanSnapshot para Contexto da IA

## Resumo

Este documento define como enriquecer o `PlanSnapshot` usado no prompt da IA com tres sinais operacionais pedidos pelo proprio fluxo de coaching:

- ultima carga relevante por exercicio do treino de hoje
- aderencia dos ultimos 7 dias para treino e nutricao
- tendencia semanal de peso

O objetivo nao e expandir a UI publica, nem mudar a UX do plano no app. O foco e melhorar a qualidade do contexto que a IA recebe para responder com mais precisao, menos chamadas de tool e mais senso de continuidade.

## Objetivos

- Fazer a IA enxergar rapidamente o contexto de execucao recente sem precisar investigar o banco a cada resposta
- Reutilizar fontes oficiais ja existentes sempre que houver calculo consolidado no sistema
- Preservar o `PlanSnapshot` como contrato unico de contexto de plano para o prompt
- Evitar duplicar motores analiticos paralelos ao TDEE/metabolismo
- Manter o snapshot compacto, seguro para prompt e resiliente a dados incompletos

## Fora de Escopo

- Exibir esses novos sinais na UI do plano ou em outras telas
- Criar novos endpoints publicos so para esse enriquecimento
- Persistir esses sinais dentro do plano ativo
- Recalcular localmente metricas que ja possuem fonte oficial consolidada
- Criar um score sofisticado multi-fator de aderencia ponderada

## Problema Atual

Hoje o `PlanSnapshot` entregue ao prompt resume:

- titulo e objetivo do plano
- periodo e status
- foco atual
- treino e nutricao do dia em formato textual
- proximos dias
- ultimo checkpoint
- restricoes e ajuste pendente

Esse snapshot e util para direcao estrategica, mas insuficiente para coaching operacional mais preciso. A IA sabe qual treino prescrito existe, mas nao sabe automaticamente:

- qual foi a ultima carga usada naquele exercicio
- se o usuario vem aderindo ao treino e a nutricao
- se o peso esta de fato subindo, descendo ou andando de lado em tendencia

O resultado e mais necessidade de chamada de tools e mais risco de resposta generica.

## Decisao de Arquitetura

Adotar um enriquecimento do `PlanSnapshot` via um agregador dedicado de contexto de coaching. O snapshot continua sendo o contrato unico entregue ao prompt, mas passa a incorporar dados estruturados derivados de fontes operacionais existentes.

### Abordagens consideradas

#### 1. Enriquecer tudo dentro de `build_plan_prompt_snapshot`

Pros:

- menor numero de arquivos
- implementacao inicial mais direta

Contras:

- aumenta acoplamento do `plan_service` com treino, nutricao e metabolismo
- mistura montagem de contrato com logica analitica

#### 2. Criar um agregador dedicado de coaching context

Pros:

- separa responsabilidades
- facilita testes
- deixa claro o que e reutilizacao de fonte oficial e o que e derivacao nova

Contras:

- adiciona uma camada nova

#### 3. Persistir sinais no proprio plano

Pros:

- leitura barata do snapshot

Contras:

- dados envelhecem
- exige sincronizacao
- piora a confiabilidade do contexto da IA

### Decisao

Adotar a abordagem `2`.

O sistema deve criar um agregador dedicado para montar o contexto de coaching e injeta-lo no `PlanSnapshot`. O `PlanSnapshot` continua sendo o unico contrato que o prompt consome, mas ele deixa de ser apenas um resumo textual e passa a carregar sinais operacionais estruturados.

## Principios

- `PlanSnapshot` continua sendo a unica fonte de contexto de plano injetada no prompt
- sempre reutilizar fonte oficial existente antes de criar novo calculo
- quando nao houver dado suficiente, omitir ou marcar como indisponivel em vez de inferir demais
- o formatter do prompt deve produzir texto curto, objetivo e acionavel
- o enriquecimento nao pode exigir alteracao de comportamento do usuario nem do fluxo de aprovacao do plano

## Fontes Oficiais por Sinal

### 1. Tendencia semanal de peso

Fonte oficial: servico de metabolismo / `AdaptiveTDEEService`.

Justificativa:

- o sistema ja calcula `weight_change_per_week`
- a API e o dashboard ja usam esse dado como sinal oficial
- recalcular isso no contexto do plano criaria duplicidade e risco de divergencia

Regra:

- o `PlanSnapshot` deve consumir o valor final vindo da fonte oficial de metabolismo
- o snapshot nao deve recalcular tendencia semanal de peso

### 2. Aderencia de nutricao 7d

Fonte preferencial: dados ja derivados de `NutritionRepository` quando reaproveitaveis.

Justificativa:

- ja existe `weekly_adherence`, mas ele representa a semana corrente por dia da semana e nao exatamente uma janela movel de 7 dias formatada para o snapshot
- ainda assim, a mesma base de logs deve ser reaproveitada

Regra:

- o agregador pode derivar o percentual de aderencia 7d a partir dos logs de nutricao
- nao precisa criar um novo sistema de scoring, apenas um percentual simples e deterministico

### 3. Aderencia de treino 7d

Fonte: `workout_logs` + plano ativo.

Justificativa:

- nao existe uma fonte unica pronta no contexto do plano para percentual de aderencia 7d de treino
- a aderencia depende tanto da prescricao do plano quanto da execucao registrada

Regra:

- o agregador deve calcular a aderencia a partir dos dias planejados para treino dentro da janela e dos logs de treino existentes

### 4. Last load por exercicio

Fonte: historico de `workout_logs`.

Justificativa:

- os logs ja armazenam `weights_per_set`
- nao existe um indice dedicado de `last_weight`, mas o dado bruto necessario ja existe

Regra:

- o agregador deve buscar a ultima carga relevante por exercicio do treino de hoje a partir do historico recente

## Contrato Desejado do Snapshot

O `PlanSnapshot` deve continuar compacto, mas ganhar campos estruturados adicionais.

### Campos novos de alto nivel

- `today_training_context`
- `adherence_7d`
- `weight_trend_weekly`

### Estrutura conceitual sugerida

#### `today_training_context`

- lista de exercicios do treino de hoje
- para cada exercicio:
  - `exercise_name`
  - `prescribed_sets`
  - `prescribed_reps`
  - `load_guidance`
  - `last_load_kg` ou `last_load_text`
  - `last_performed_at`

#### `adherence_7d`

- `training_percent`
- `nutrition_percent`
- `window_start`
- `window_end`

#### `weight_trend_weekly`

- `value_kg_per_week`
- `source`

O campo `source` e util apenas para rastreabilidade interna e testes. O formatter do prompt nao precisa expor isso ao modelo em texto se nao agregar valor.

## Regras de Calculo

### Last load por exercicio

- considerar apenas exercicios do `today_training` do plano ativo
- buscar historico recente em janela limitada, preferencialmente `90 dias`
- casar exercicios primariamente por nome normalizado
- usar a ultima sessao em que o exercicio apareceu, e nao o maior PR historico
- dentro dessa ultima sessao, extrair a maior carga valida do exercicio como referencia pratica
- ignorar pesos zerados ou ausentes
- se nao houver historico confiavel, nao fabricar recomendacao; apenas omitir `last_load`

Racional:

- para coaching diario, a ultima exposicao recente e mais util do que o PR absoluto

### Aderencia de nutricao 7d

- janela movel dos ultimos `7 dias`, incluindo o dia atual
- percentual = dias com log nutricional / 7
- o calculo deve ser simples: existe log do dia conta como aderencia do dia
- nao incluir peso de macros, calorias ou qualidade do log nesta V1

### Aderencia de treino 7d

- janela movel dos ultimos `7 dias`, incluindo o dia atual
- considerar apenas dias planejados como treino no plano dentro da janela
- percentual = dias planejados com treino executado / dias planejados
- dias de descanso nao contam como falha
- se nao houver treino planejado na janela, retornar `None` ou um estado equivalente a `indisponivel`, nao `0%`

### Tendencia semanal de peso

- usar diretamente `weight_change_per_week` vindo do servico de metabolismo
- manter unidade em `kg/semana`
- formatter deve exibir com sinal explicito quando positivo

## Formato do Prompt

O formatter do `PlanSnapshot` deve continuar legivel e curto. Os novos sinais devem entrar como bloco resumido, sem transformar o snapshot num dump de JSON.

### Exemplo conceitual

```text
Plano ativo: Hipertrofia com recomposicao
Objetivo: ganhar massa mantendo controle de gordura
Periodo do plano: 2026-04-01 a 2026-05-01
Status: active
Foco atual: consistencia e progressao
Treino de hoje: Upper A
Contexto do treino de hoje:
- Supino reto: 3x8-10 | ultima carga registrada 80 kg em 2026-04-18
- Remada curvada: 3x8-10 | ultima carga registrada 70 kg em 2026-04-18
Nutricao de hoje: 2400 kcal / 160g proteina
Aderencia 7d: treino 100% | nutricao 86%
Tendencia de peso: -0.20 kg/semana
Proximos dias: ...
Ultimo checkpoint: ...
Restricoes criticas: ...
Ajuste pendente: nenhum
```

## Comportamento com Dados Incompletos

- sem plano ativo: comportamento atual permanece
- sem treino de hoje estruturado: nao gerar `today_training_context`
- sem historico de exercicio: exercicio aparece sem `last_load`
- sem dados suficientes de metabolismo: usar o fallback oficial do servico de metabolismo, nunca recalculo paralelo
- sem treino planejado na janela: aderencia de treino deve ficar indisponivel
- sem logs nutricionais na janela: aderencia de nutricao pode ser `0%`

## Componentes a Ajustar

### Backend de plano

- evoluir o modelo `PlanSnapshot`
- criar servico/agregador de coaching context
- atualizar o builder do snapshot para consumir o agregador
- atualizar o formatter textual do snapshot

### Fontes de dados reutilizadas

- `AdaptiveTDEEService` para tendencia semanal de peso
- repositorio de nutricao para logs recentes
- repositorio de treinos para historico recente e cargas por exercicio

### Prompt

- manter um unico ponto de injecao de `plan_section`
- somente o texto formatado do snapshot muda

## Testes Necessarios

### Unitarios

- snapshot sem plano continua retornando `None`
- snapshot com plano agora inclui `adherence_7d`, `weight_trend_weekly` e contexto de treino
- `last_load` usa ultima sessao relevante e ignora pesos zerados
- `last_load` nao usa PR historico antigo quando existe sessao mais recente do mesmo exercicio
- `last_load` escolhe a ultima sessao correta quando o exercicio aparece em multiplos treinos no historico
- `last_load` ignora sessoes fora da janela configurada de busca
- `last_load` ignora exercicios sem nome ou com nome vazio no historico
- `last_load` nao quebra quando `reps_per_set` e `weights_per_set` possuem tamanhos diferentes
- `last_load` trata exercicios com pesos parcialmente preenchidos sem estourar indice
- `last_load` retorna ausencia de contexto quando so existem pesos `0`, `None` ou lista vazia
- `last_load` nao contamina um exercicio com carga de outro exercicio na mesma sessao
- comparacao de exercicios por nome normalizado funciona para variacoes triviais de espaco e caixa
- comparacao de exercicios nao mistura exercicios diferentes com nomes parecidos demais
- quando dois exercicios do treino de hoje compartilham prefixos semelhantes, cada um recebe apenas seu proprio historico
- contexto do treino de hoje preserva a ordem dos exercicios prescritos no plano
- contexto do treino de hoje continua sendo gerado mesmo quando apenas parte dos exercicios possui historico
- aderencia de treino nao pune dias de descanso
- aderencia de treino fica indisponivel quando nao ha treino planejado na janela
- aderencia de treino fica indisponivel quando nao existe `upcoming_days` suficiente para inferir planejamento na janela
- aderencia de treino retorna `100%` quando todos os dias planejados tiveram execucao
- aderencia de treino retorna percentual parcial correto quando apenas parte dos dias planejados teve execucao
- aderencia de treino nao contabiliza treino extra em dia nao planejado como cumprimento de outro dia
- aderencia de treino nao considera treino duplicado no mesmo dia como aderencia maior que `100%`
- aderencia de treino lida corretamente com janela cruzando virada de semana e virada de mes
- aderencia de treino lida com usuario novo que tem plano ativo, mas nenhum workout log
- aderencia de treino lida com usuario sem plano operacional detalhado sem explodir o snapshot
- aderencia de nutricao conta percentual simples sobre 7 dias
- aderencia de nutricao retorna `0%` para usuario sem logs nutricionais na janela
- aderencia de nutricao retorna percentual correto para usuario com apenas `1`, `3`, `5` ou `7` dias logados
- aderencia de nutricao ignora logs fora da janela movel de 7 dias
- aderencia de nutricao nao duplica contagem quando houver mais de um registro no mesmo dia por legado ou dado inconsistente
- aderencia de nutricao lida com usuario novo sem qualquer historico
- tendencia semanal de peso reutiliza a fonte do metabolismo
- tendencia semanal de peso usa fallback oficial do metabolismo quando nao ha dados suficientes
- tendencia semanal de peso nao recalcula localmente quando a fonte oficial retorna valor valido
- tendencia semanal de peso lida com valor `0.0` como dado valido, nao como ausencia
- tendencia semanal de peso preserva sinal positivo, negativo e neutro na formatacao
- snapshot continua valido para usuario sem peso, sem nutricao e sem treino historico
- snapshot continua valido quando apenas um dos tres sinais novos esta disponivel
- snapshot continua valido quando todos os sinais novos estao indisponiveis
- formatter omite linhas opcionais sem gerar texto quebrado, duplicado ou ambiguidade
- formatter textual inclui novos blocos sem quebrar o formato atual
- formatter textual nao gera dump verboso de lista ou dicionario bruto no prompt
- formatter textual mantem saida compacta mesmo com varios exercicios no treino de hoje
- formatter textual nao inventa datas, cargas ou percentuais ausentes
- formatter textual usa separacao consistente entre plano base e sinais enriquecidos

### Casos de uso prioritarios a automatizar

- usuario avancado com historico rico: recebe `last_load` em todos os exercicios principais, aderencia parcial e tendencia negativa de peso
- usuario iniciante com plano ativo recem-criado: recebe snapshot sem `last_load`, com aderencias baixas ou indisponiveis e sem quebra no prompt
- usuario com nutricao consistente e treino inconsistente: snapshot mostra assimetria real entre `nutrition_percent` e `training_percent`
- usuario com treino consistente e sem logs nutricionais: snapshot mostra `training_percent` valido e `nutrition_percent` em `0%`
- usuario em manutencao com `weight_change_per_week = 0.0`: snapshot mostra estabilidade sem tratar o valor como ausente
- usuario com nomes de exercicio variando levemente entre plano e log: matching simples funciona sem fuzzy matching agressivo
- usuario com exercicios distintos mas semanticamente proximos: snapshot nao cruza historico indevido entre exercicios diferentes
- usuario sem qualquer dado historico: IA ainda recebe o plano base com enriquecimento ausente de forma segura

### Integracao

- tool `get_plan_prompt_snapshot` retorna o novo texto enriquecido
- injecao do snapshot no prompt do treinador continua funcionando
- o sistema se comporta bem com dados parciais ou ausentes

## Riscos

- casamento ingenuo por nome de exercicio pode falhar em variantes de nomenclatura
- o builder do plano pode ficar lento se buscar historico demais em cada mensagem
- misturar logica de calendario do plano com janela movel de 7 dias exige regra clara para nao superestimar aderencia

## Mitigacoes

- comecar com normalizacao simples e previsivel de nome, sem fuzzy matching agressivo
- limitar historico de busca de treino por janela e quantidade
- isolar a logica de agregacao em servico proprio com testes dedicados
- tratar indisponibilidade de dado como estado valido, nao como erro

## Decisoes Fechadas

- o enriquecimento e apenas para a IA, nao para a UI publica
- o contrato unico continua sendo o `PlanSnapshot`
- `weight_trend_weekly` deve reutilizar a fonte oficial do metabolismo/TDEE
- `last_load` deve refletir a ultima sessao relevante, nao o PR historico
- aderencia 7d deve ser simples e deterministica nesta primeira entrega

## Perguntas em Aberto para Implementacao

- qual estrategia minima de normalizacao de nome de exercicio sera suficiente para a V1
- qual janela ideal de busca de historico de treino oferece bom equilibrio entre relevancia e custo
- se o formatter deve mostrar data da ultima carga em todos os casos ou apenas quando houver valor claro

Estas perguntas sao de nivel de implementacao e nao bloqueiam o plano. O desenho funcional ja esta fechado.
