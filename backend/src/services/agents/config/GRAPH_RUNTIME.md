# Conversation Graph Runtime

Esta documentacao descreve o runtime atual do LangGraph usado no chat principal.
Ela complementa os manifests em `nodes/*.json`, os prompts em `prompts/*.md`
e o codigo em `backend/src/services/graph/conversation_graph.py`.

## Objetivo

Substituir o fluxo monolitico por uma orquestracao explicita, auditavel e
com contratos claros entre nos.

Principios:

- cada no tem um papel unico e delimitado
- prompts ficam versionados no repositorio
- contexto e peer inputs sao injetados por allowlist
- persistencia relevante e executada de forma deterministica no runtime
- o plano e tratado como nucleo do produto
- a persona do entrenador fica apenas no `coach_reply`; os demais nos recebem contexto tecnico, nao voz/persona

## Ordem de execucao

Ordem fixa do grafo:

1. `session_context`
2. `prompt_security`
3. `intent_router`
4. `training_specialist` se a intencao exigir treino
5. `nutrition_specialist` se a intencao exigir nutricao
6. `plan_specialist`
7. `coach_reply`
8. `memory_hub`

Regras de roteamento:

- `prompt_security` roda sempre antes de qualquer no de dominio.
- se `prompt_security` bloquear a mensagem, o fluxo nao passa por treino,
  nutricao, plano ou sintese.
- `training_specialist` roda para intents `training`, `plan` e `multi_domain`.
- `nutrition_specialist` roda para intents `nutrition`, `plan` e `multi_domain`.
- `plan_specialist` roda sempre que a mensagem nao foi bloqueada.
- se `plan_specialist` marcar `needs_revision=true`, treino e nutricao podem
  rodar mais uma vez no mesmo turno para refinar o caso antes da sintese final.
- `coach_reply` produz a resposta final ao usuario, incluindo a voz/persona do entrenador.
- `memory_hub` roda por ultimo para registrar memoria e agenda sem
  alterar a resposta final.

## O que cada no faz

### `session_context`

Responsabilidade:

- hidratar contexto deterministico do turno em codigo (sem LLM)
- carregar perfil do usuario e do entrenador
- carregar agenda, metabolismo, historico e plano ativo
- produzir `runtime_context_json`
- derivar sinais objetivos do ciclo de vida do plano

Saidas relevantes:

- `shared_context.input_data`
- `shared_context.plan_lifecycle`

Este no NAO faz inferencia LLM. Seu unico output e `state.node_outputs["session_context"] = "hydrated"`.

### `prompt_security`

Responsabilidade:

- bloquear ou sanitizar tentativas de prompt injection
- impedir leak de instrucoes internas
- manter o fluxo dentro do escopo permitido

Detalhes:

- ha um filtro deterministico por regex antes da LLM
- o no completa a classificacao em JSON (`safe` ou `blocked`)

Modelo default:

- `openai/gpt-5-nano`

### `intent_router`

Responsabilidade:

- classificar a intencao operacional do turno

Intents suportadas:

- `training`
- `nutrition`
- `plan`
- `multi_domain`
- `general`

Regra pratica importante:

- quando treino e nutricao aparecem ambos como partes materiais da mesma mensagem, o roteador deve preferir `multi_domain`
- `nutrition` fica para mensagens cujo foco principal seja aderencia alimentar
- `training` fica para mensagens cujo foco principal seja treino, progressao ou sessao
- `plan` fica para mudancas estruturais, renovacao ou discovery do plano

Modelo default:

- `openai/gpt-5-nano`

### `training_specialist`

Responsabilidade:

- analisar e registrar treino
- comparar sessoes equivalentes
- classificar progresso
- emitir conflito estrutural de plano quando houver
- nao recebe a persona do treinador; opera em linguagem tecnica

Tools principais:

- `save_workout`
- `get_workouts`
- `get_workouts_raw`
- `list_hevy_routines`
- `get_hevy_routine_detail`
- `trigger_hevy_import`
- `save_body_composition`
- `get_body_composition`
- `get_body_composition_raw`

Contrato de saida:

- `analysis_text`
- `domain_status`
- `plan_signal`
- `memory_candidates`
- `event_candidates`
- event candidates aceitam opcionalmente `event_recurrence` quando a intencao for recorrente

Modelo default:

- `deepseek/deepseek-v4-flash`

### `nutrition_specialist`

Responsabilidade:

- analisar e registrar nutricao
- comparar ingestao com metas oficiais
- validar numeros contra metabolismo oficial
- emitir conflito estrutural de plano quando houver
- nao recebe a persona do treinador; opera em linguagem tecnica

Tools principais:

- `save_daily_nutrition`
- `get_nutrition`
- `get_nutrition_raw`
- `sync_nutrition_text`
- `get_metabolism_data`
- `get_user_goal`

Contrato de saida:

- `analysis_text`
- `domain_status`
- `plan_signal`
- `memory_candidates`
- `event_candidates`
- event candidates aceitam opcionalmente `event_recurrence` quando a intencao for recorrente

Modelo default:

- `deepseek/deepseek-v4-flash`

### `plan_specialist`

Responsabilidade:

- dono do ciclo de vida do plano
- discovery quando nao existe plano
- revisao quando treino/nutricao pedem ajuste estrutural
- renovacao quando o plano vence ou o objetivo foi atingido
- persistencia real do plano
- nao recebe a persona do treinador; decide o plano em linguagem tecnica

Tools principais:

- `get_plan`
- `upsert_plan`
- `plan_help`
- `get_user_goal`
- `update_user_goal`
- `get_metabolism_data`

Contrato de saida:

- `plan_status`
- `reason`
- `technical_summary` (texto tecnico interno, sem vocativo ou tom de coaching)
- `needs_revision`
- `plan_candidate`
- `memory_candidates`
- `event_candidates`
- event candidates aceitam opcionalmente `event_recurrence` quando a acao envolver revisao recorrente

Modelo default:

- `deepseek/deepseek-v4-flash`

### `coach_reply`

Responsabilidade:

- sintetizar treino, nutricao e plano em uma unica resposta final
- preservar coerencia tecnica
- aplicar a persona do entrenador sem mudar a semantica
- responder no idioma predominante da mensagem do usuario com voz nativa, sem traducao literal nem importacao de bordoes do portugues
- adaptar tambem os rotulos das secoes finais ao idioma escolhido
- preencher `coach_response` e `final_response`

Importante:

- este no substituiu o antigo `general_conversation`
- estilo e persona foram fundidos aqui para economizar uma passada completa de LLM

Formato esperado da resposta:

1. `Leitura dos dados:`
2. `Interpretacao:`
3. `Proximas acoes:`

A resposta final deve seguir o idioma predominante do usuario, mantendo os mesmos tres blocos.
Os rotulos das secoes devem ser traduzidos para o idioma escolhido (pt-BR, en-US ou es-ES).

Modelo default:

- `deepseek/deepseek-v4-flash`

### `memory_hub`

Responsabilidade:

- decidir e executar memoria/agenda quando isso melhora turnos futuros

Politica de execucao:

- primeiro consome `persistence_candidates` estruturados vindos dos nos anteriores
- so recorre a LLM quando nao ha candidatos estruturados suficientes
- executa a acao em codigo com checagem de deduplicacao

Escopo:

- memoria duravel
- agenda e follow-up

Modelo default:

- `openai/gpt-5-nano`

## Fluxo de dados

### Estado compartilhado

O `GraphState` carrega:

- `request`
- `security`
- `routing`
- `shared_context`
- `node_outputs`
- `node_metadata`
- `tools_called`
- `persistence_actions`
- `coach_response`
- `final_response`

### Catalogo de contexto

Antes de cada chamada de LLM, o runtime monta um catalogo com blocos como:

- `request`
- `user_profile`
- `trainer_identity`
- `trainer_persona`
- `agenda`
- `active_plan`
- `metabolism`
- `history_summary`
- `training_analysis`
- `nutrition_analysis`
- `plan_workspace`
- `plan_lifecycle`
- `coach_response`

Cada no recebe apenas os blocos listados em seu manifesto `context_blocks`.

### Peer inputs

Os outputs textuais de outros nos entram em `PEER_INPUTS` somente quando o
manifesto do no atual lista esses peers em `peer_inputs`.

## Fluxo de persistencia

Existem dois niveis de persistencia:

### Persistencia de dominio

Executada pelo proprio no especialista:

- treino: `save_workout`, `save_body_composition`
- nutricao: `save_daily_nutrition`
- plano: `upsert_plan`, `update_user_goal`

### Persistencia de memoria e agenda

Executada no `memory_hub`:

- `search_memory`, `save_memory`, `update_memory`, `delete_memory`
- `list_events`, `create_event`, `update_event`, `delete_event`

O runtime prioriza candidatos estruturados:

- `memory_candidates`
- `event_candidates`

Para eventos recorrentes, o runtime usa `event_recurrence` quando disponivel e so envia `date` para a tool quando houver uma data ISO concreta.

Se nenhum candidato valido existir, o `memory_hub` usa sua propria LLM
para planejar a acao.

## Modelos atuais por no

| No | Modelo |
|---|---|
| `session_context` | sem LLM (codigo puro) |
| `prompt_security` | `openai/gpt-5-nano` |
| `intent_router` | `openai/gpt-5-nano` |
| `training_specialist` | `deepseek/deepseek-v4-flash` |
| `nutrition_specialist` | `deepseek/deepseek-v4-flash` |
| `plan_specialist` | `deepseek/deepseek-v4-flash` |
| `coach_reply` | `deepseek/deepseek-v4-flash` |
| `memory_hub` | `openai/gpt-5-nano` |

## Onde editar

- manifests: `backend/src/services/agents/config/nodes/*.json`
- prompts: `backend/src/services/agents/config/prompts/*.md`
- runtime: `backend/src/services/graph/conversation_graph.py`
- contrato de contexto: `backend/src/services/PROMPT_CONTEXT.md`

## Como validar

Minimo recomendado:

1. `cd backend && .venv/bin/pytest tests/unit/services/test_agent_config_registry.py tests/unit/services/test_conversation_graph.py tests/unit/core/test_experimental_graph_flag.py`
2. `cd backend && .venv/bin/ruff check src tests`
3. `cd backend && .venv/bin/pylint src`

Validacao manual importante:

- inspecionar traces `graph.*`
- confirmar ordem real dos nos
- confirmar tools chamadas por no
- confirmar que `coach_reply` ja entrega a resposta final sem segunda passada
