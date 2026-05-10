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

Ordem fixa do grafo (todos os nos executam uma unica vez por turno, em ordem estritamente linear):

1. `session_context`
2. `prompt_security`
3. `training_specialist`
4. `nutrition_specialist`
5. `plan_specialist`
6. `coach_reply`
7. `memory_hub`

Regras de execucao:

- A ordem de execucao e a fonte unica de verdade. Nao ha chamadas extras de `coach_reply`
  ou `memory_hub` fora do loop.
- Todos os nos especialistas rodam em toda mensagem que passe por `prompt_security`.
- Se `prompt_security` bloquear a mensagem, o fluxo e interrompido antes de `training_specialist`.
  `coach_reply` e `memory_hub` nao executam e nao geram efeito colateral.
- Cada especialista decide internamente se age ou emite no-op (`action_status: no_action_needed`).
- `coach_reply` sintetiza as saidas nao-vazias dos especialistas em uma unica resposta ao usuario.
- `memory_hub` roda por ultimo para registrar memoria e agenda sem alterar a resposta final.

### Resolucao de pending_action

Apos os tres especialistas e antes do `coach_reply`, o runtime resolve
`specialist_pending_actions` em um unico `pending_action` usando prioridade
deterministica:

1. `domain_execution` (maior prioridade)
2. `plan_discovery`
3. `plan_review`
4. `domain_analysis`
5. `none` (sem acao pendente)

O vencedor e escrito em `state.conversation_state["pending_action"]`.
Isso substitui o antigo modelo de roteamento por `primary_owner`.

## O que cada no faz

### `session_context`

Responsabilidade:

- hidratar contexto deterministico do turno em codigo (sem LLM)
- carregar perfil do usuario e do entrenador
- carregar agenda, metabolismo, historico e plano ativo
- produzir `runtime_context_json`
- derivar sinais objetivos do ciclo de vida do plano
- recuperar `conversation_state` do turno anterior (snapshot persistido como SYSTEM message)

Saidas relevantes:

- `shared_context.input_data`
- `shared_context.plan_lifecycle`
- `shared_context.conversation_state` (restaurado do historico)

Este no usa LLM apenas para sanitizar o historico (`history_summary_neutral`).
Seu output principal e `state.node_outputs["session_context"] = "hydrated"`.

### `prompt_security`

Responsabilidade:

- bloquear ou sanitizar tentativas de prompt injection
- impedir leak de instrucoes internas
- manter o fluxo dentro do escopo permitido

Detalhes:

- ha um filtro deterministico por regex antes da LLM
- o no completa a classificacao em JSON (`safe` ou `blocked`)

Modelo default:

- `google/gemini-2.5-flash-lite`

### `training_specialist`

Responsabilidade:

- analisar e registrar treino
- comparar sessoes equivalentes
- classificar progresso
- emitir conflito estrutural de plano quando houver
- se a mensagem nao for sobre treino, emitir `action_status: no_action_needed` e texto vazio
- nao recebe a persona do treinador; opera em linguagem tecnica

Tools principais:

- `save_workout`
- `get_workouts`
- `list_hevy_routines`
- `get_hevy_routine_detail`
- `trigger_hevy_import`
- `create_hevy_routine`
- `update_hevy_routine`
- `search_hevy_exercises`
- `replace_hevy_exercise`
- `set_routine_rest_and_ranges`
- `save_body_composition`
- `get_body_composition`

Contrato de saida:

- `action_type`
- `action_status` (`executed`, `needs_user_input`, `no_action_needed`)
- `domain_status`
- `technical_summary`
- `missing_inputs`
- `plan_signal`
- `pending_action` (dict com `kind`, `status`, `missing_slots`)
- `memory_candidates`
- `event_candidates`

Modelo default:

- `google/gemini-3.1-flash-lite-preview`

### `nutrition_specialist`

Responsabilidade:

- analisar e registrar nutricao
- comparar ingestao com metas oficiais
- validar numeros contra metabolismo oficial
- emitir conflito estrutural de plano quando houver
- se a mensagem nao for sobre nutricao, emitir `action_status: no_action_needed` e texto vazio
- nao recebe a persona do treinador; opera em linguagem tecnica

Tools principais:

- `save_daily_nutrition`
- `get_workouts`
- `get_nutrition`
- `sync_nutrition_text`
- `get_metabolism_data`
- `get_user_goal`
- `update_tdee_params`

Contrato de saida:

- `action_type`
- `action_status` (`executed`, `needs_user_input`, `no_action_needed`)
- `domain_status`
- `technical_summary`
- `missing_inputs`
- `plan_signal`
- `pending_action` (dict com `kind`, `status`, `missing_slots`)
- `memory_candidates`
- `event_candidates`

Modelo default:

- `google/gemini-3.1-flash-lite-preview`

### `plan_specialist`

Responsabilidade:

- dono do ciclo de vida do plano
- discovery quando nao existe plano
- revisao quando treino/nutricao pedem ajuste estrutural
- renovacao quando o plano vence ou o objetivo foi atingido
- persistencia real do plano
- se a mensagem nao envolve plano ou revisao, emitir `action_status: no_action_needed` e texto minimo
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
- `action_status`
- `reason`
- `technical_summary` (texto tecnico interno, sem vocativo ou tom de coaching)
- `needs_revision`
- `plan_candidate`
- `pending_slots`
- `resolved_slots`
- `pending_action` (dict com `kind`, `status`, `missing_slots`)
- `memory_candidates`
- `event_candidates`

Modelo default:

- `openai/gpt-oss-120b` (com `provider_sort: "throughput"`)

### `coach_reply`

Responsabilidade:

- sintetizar treino, nutricao e plano em uma unica resposta final
- preservar coerencia tecnica
- aplicar a persona do entrenador sem mudar a semantica
- responder no idioma predominante da mensagem do usuario com voz nativa, sem traducao literal nem importacao de bordoes do portugues
- adaptar tambem os rotulos das secoes finais ao idioma escolhido
- ignorar saidas de especialistas que emitiram no-op

Importante:

- este no substituiu o antigo `general_conversation`
- estilo e persona foram fundidos aqui para economizar uma passada completa de LLM
- nao possui tools e nao tem autoridade operacional

Modelo default:

- `google/gemini-3.1-flash-lite-preview`

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

- `google/gemini-3.1-flash-lite-preview`

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
- `specialist_pending_actions` (dict[str, dict] — cada especialista sugere um `pending_action`)
- `specialist_states` (dict[str, dict] — `action_status` e `action_type` por no)
- `conversation_state` (dict — `pending_action`, `last_action_status`, `active_domain`)

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
- `history_summary_neutral`
- `training_analysis`
- `nutrition_analysis`
- `plan_workspace`
- `plan_lifecycle`
- `coach_response`
- `conversation_state` (JSON serializado do estado cross-turn)
- `security_result`

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
| `session_context` | `qwen/qwen3-next-80b-a3b-instruct` (apenas sanitizacao de historico) |
| `prompt_security` | `google/gemini-2.5-flash-lite` |
| `training_specialist` | `google/gemini-3.1-flash-lite-preview` |
| `nutrition_specialist` | `google/gemini-3.1-flash-lite-preview` |
| `plan_specialist` | `openai/gpt-oss-120b` (`provider_sort: "throughput"`) |
| `coach_reply` | `google/gemini-3.1-flash-lite-preview` |
| `memory_hub` | `google/gemini-3.1-flash-lite-preview` |

## Estado cross-turn

Apos cada turno, um snapshot `[GRAPH_STATE_V1]` e persistido como SYSTEM message no historico de chat (`conversation_contract.py`). O snapshot contem:

- `active_domain` (derivado deterministicamente apos os especialistas executarem)
- `pending_action` (resolvido por prioridade pelos especialistas)
- `last_action_status`

`active_domain` e derivado apos `plan_specialist`, durante `_resolve_pending_actions()`:
- Se `pending_action.kind` for `plan_discovery`/`plan_review` -> `plan`
- Se `plan_specialist` atuou materialmente -> `plan`
- Se `training_specialist` e `nutrition_specialist` atuaram -> `multi_domain`
- Se so `training_specialist` atuou -> `training`
- Se so `nutrition_specialist` atuou -> `nutrition`
- Se nenhum atuou -> `general`

No turno seguinte, `session_context` recupera o snapshot e o injeta em
`state.conversation_state`. Cada especialista pode ler `conversation_state`
via `context_blocks` para manter continuidade. Nao ha mais `primary_owner`,
`interaction_mode`, ou `secondary_nodes`.

Snapshots antigos que contenham `primary_owner` e `interaction_mode` ainda
sao parseados com sucesso (backward compatible).

## Onde editar

- manifests: `backend/src/services/agents/config/nodes/*.json`
- prompts: `backend/src/services/agents/config/prompts/*.md`
- runtime: `backend/src/services/graph/conversation_graph.py`
- contrato de estado: `backend/src/services/graph/conversation_contract.py`
- contrato de contexto: `backend/src/services/PROMPT_CONTEXT.md`

## Como validar

Minimo recomendado:

1. `cd backend && .venv/bin/pytest tests/unit/services/test_agent_config_registry.py tests/unit/services/test_conversation_graph.py tests/unit/services/test_conversation_contract.py tests/unit/services/test_node_tool_policy.py tests/unit/core/test_experimental_graph_flag.py`
2. `cd backend && .venv/bin/ruff check src tests`
3. `cd backend && .venv/bin/pylint src`

Validacao manual importante:

- inspecionar traces `graph.*`
- confirmar ordem real dos nos (linear, sem saltos condicionais)
- confirmar tools chamadas por no
- confirmar que `coach_reply` ja entrega a resposta final sem segunda passada
- confirmar que especialistas sem acao relevante emitem `no_action_needed`