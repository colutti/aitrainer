# Session Context + Coach Reply + Memory Hub

## Resumo
Este plano remove redundância semântica, reforça separação de responsabilidades e renomeia nós com linguagem de produto:
- `turn_context` -> `session_context` (hidratação determinística de dados do turno).
- `general_conversation` -> `coach_reply` (único nó que responde ao usuário com persona).
- `persistence_guard` -> `memory_hub` (memória/eventos de continuidade).
- `plan_specialist` deixa de produzir texto de persona para usuário e passa a produzir somente saída técnica interna.

## Explicação simples
- Hoje especialistas já recebem quase todo o contexto bruto (`request`, `active_plan`, `metabolism`, etc.).
- Além disso, recebem `context_summary` gerado por `turn_context`.
- Isso cria sobreposição.

Decisão:
1. Manter o primeiro nó só para hidratar dados uma vez (evitar buscas repetidas no banco).
2. Remover resumo LLM intermediário (`context_summary`).
3. Manter análise de domínio nos especialistas.
4. Garantir que somente `coach_reply` fale com o usuário.

## Mudanças de implementação

### 1) Rename oficial dos nós (produto)
- `turn_context` -> `session_context`
- `general_conversation` -> `coach_reply`
- `persistence_guard` -> `memory_hub`

Aplicar rename end-to-end em:
- `NODE_ORDER`
- métodos `_node_*` no runner
- `state.node_outputs[...]`
- `peer_inputs` nos manifests
- logs/traces (`graph.node_started`, `graph.node_completed`, `graph.turn_completed`, `run_name=graph.*`, `mode=graph:*`)
- `output_preview`/metadata de debug por nó
- documentação de runtime/config

### 2) `session_context` sem LLM
- Em `backend/src/services/graph/conversation_graph.py`:
  - remover chamada `_run_llm_node(...)` no nó de contexto inicial.
  - remover gravação de `context_summary` em `shared_context`.
  - definir `state.node_outputs["session_context"]` como marcador técnico (ex.: `"hydrated"`).
- Preservar hidratação atual:
  - perfil do usuário/treinador,
  - metabolismo,
  - plano,
  - agenda,
  - histórico,
  - `runtime_context_json`,
  - `plan_lifecycle`.

### 3) Remover dependência de `context_summary`
- Atualizar manifests em `backend/src/services/agents/config/nodes/*.json` para remover `context_summary` dos `context_blocks`.
- Atualizar prompts em `backend/src/services/agents/config/prompts/*.md` removendo referência a `context_summary` em "Allowed context".

### 4) `plan_specialist` técnico, sem fala ao usuário
- Atualizar prompt de `plan_specialist` para proibir vocativo/nome do usuário e tom de coaching.
- Trocar contrato de saída:
  - de `user_reply` para `technical_summary`.
- No runtime:
  - parsear `technical_summary`,
  - preencher `state.node_outputs["plan_specialist"]` com conteúdo técnico interno.

### 5) Papel do `coach_reply`
- `coach_reply` permanece como único nó autorizado a resposta final de usuário.
- Especialistas (`training`, `nutrition`, `plan`) permanecem com `persona_mode: none` e saída interna técnica.

## Contratos e interfaces afetados
- `backend/src/services/agents/config/nodes/*.json`
  - rename dos `node_name` afetados.
  - ajuste de `peer_inputs` para novos nomes.
  - remoção de `context_summary` de `context_blocks`.
- `backend/src/services/agents/config/prompts/*.md`
  - remover `context_summary` e alinhar nomenclatura dos nós.
- `backend/src/services/graph/conversation_graph.py`
  - atualizar dispatch de nós, parse de outputs e nomes em metadata/debug.
- endpoint de debug de turno (payload de nós) continua o mesmo contrato externo, com novos `node_name` nos itens internos.

## Testes

### Automatizáveis
1. Unitário do grafo: `session_context` não chama LLM.
2. Unitário do grafo: `runtime_context_json` e `plan_lifecycle` permanecem preenchidos.
3. Unitário do `plan_specialist`: parse de `technical_summary` e ausência de `user_reply`.
4. Unitário/config: manifests carregam com novos nomes e `peer_inputs` válidos.
5. Regressão fluxo `nutrition`: `save_daily_nutrition` continua sendo chamado quando entrada é suficiente.
6. Regressão fluxo `multi_domain`: ordem e execução preservadas com novos nomes.

### Gates obrigatórios backend
- `cd backend && .venv/bin/ruff check src tests`
- `cd backend && .venv/bin/pylint src`
- testes unitários do grafo/config.

## Critérios de aceite
- `session_context` não faz inferência por LLM.
- Não existe `context_summary` injetado nos nós.
- `plan_specialist` não gera texto conversacional para usuário.
- Apenas `coach_reply` gera resposta final ao usuário.
- Nomes de nós no runtime/config/docs refletem os novos IDs (`session_context`, `coach_reply`, `memory_hub`).

## Riscos e mitigação
- Risco: quebra de wiring por rename parcial.
- Mitigação: aplicar rename atômico em runtime + manifests + prompts + docs, com testes de carregamento/config e fluxo.

## Observação
Este plano é de backend/orquestração e não altera a persistência já validada do domínio (ex.: `save_daily_nutrition` no especialista de nutrição).
