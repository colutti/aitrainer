# Implementação de Gerenciamento Avançado de Contexto (SOTA)

Este plano visa elevar o nível de gerenciamento de memória do Agente para o estado da arte (SOTA), reduzindo alucinações de contexto e melhorando a coerência em conversas longas.

## Objetivos
1.  **Native Tool Roles:** Usar `ToolMessage` nativo (OpenAI/Gemini) para outputs de ferramentas, evitando confusão entre texto do usuário e logs de sistema.
2.  **Progressive Summarization:** Implementar uma camada intermediária de memória que resume blocos de conversa antiga *mantendo a estrutura de turnos*, antes de comprimir para texto estático.

---

## Fase 1: Native Tool Messages (Role 'tool')

O objetivo é que o modelo veja a sequência:
`User (pergunta) -> AI (tool_call) -> Tool (result) -> AI (resposta final)`
Hoje ele vê:
`User -> AI -> System(Human) -> AI`

### Mudanças Necessárias
1.  **Refatorar `AITrainerBrain._format_history_as_messages`**:
    *   Identificar mensagens de sistema que são resultados de tools.
    *   Converter para objetos `ToolMessage` do LangChain.
    *   **Desafio:** `ToolMessage` exige um `tool_call_id` que corresponda ao `tool_calls` na `AIMessage` anterior.
    *   **Solução:** Precisamos garantir que quando salvamos a mensagem da IA no Mongo (`_add_to_mongo_history`), salvamos também os `tool_calls` (IDs e argumentos). E quando salvamos o resultado da tool, salvamos o `tool_call_id`.

2.  **Schema do MongoDB (`ChatHistory`)**:
    *   Adicionar campos `tool_calls` (list de dicts) em mensagens do tipo TRAINER.
    *   Adicionar campo `tool_call_id` (str) em mensagens do tipo SYSTEM (agora TOOL).

3.  **Refatorar `LLMClient.stream_with_tools`**:
    *   Garantir que o chunk de `tool_call` recebido do provider seja capturado e retornado para ser salvo.
    *   Hoje o código parece salvar apenas o texto final. Precisamos interceptar os metadados de tool call.

---

## Fase 2: Progressive Summarization

Em vez de: `Mensagens Recentes (20) -> Resumo Texto (Infinito)`
Teremos: `Recentes (20)` -> `Resumo Estruturado (20-100)` -> `Resumo Texto (Arquivado)`

### Mudanças Necessárias
1.  **Novo Campo em `UserProfile`**:
    *   `structured_history_summary`: List[dict] (JSON reduzido).
    *   Armazena versões simplificatas das mensagens antigas. Ex: "User pediu treino" (em vez do prompt inteiro), "AI sugeriu X".

2.  **Refatorar `HistoryCompactor`**:
    *   Em vez de apenas gerar texto, ele deve primeiro tentar "comprimir" mensagens antigas em objetos menores.
    *   Exemplo: Uma Tool Call gigante de JSON vira -> `Tool: get_nutrition (19 items found)`.
    *   Somente mensagens MUITO antigas viram texto no `long_term_summary`.

---

## Detalhe da Execução (Foco na Fase 1 - Imediato)

A Fase 1 é pré-requisito crítico e resolve a "conversa torta" com tools.

### 1.1 Atualizar Modelo `ChatHistory`
Arquivo: `/backend/src/api/models/chat_history.py`

```python
class ChatHistory(BaseModel):
    # ... existentes
    tool_calls: Optional[List[Dict]] = None  # Para mensagens da IA
    tool_call_id: Optional[str] = None       # Para mensagens de Tool (antigo System)
    name: Optional[str] = None               # Nome da tool
```

### 1.2 Atualizar Persistência (`MongoDatabase`)
Garantir que salvamos e recuperamos esses campos.

### 1.3 Atualizar Injeção de Histórico (`trainer.py`)
No método `_format_history_as_messages`:

```python
if msg.tool_call_id:
    formatted_msgs.append(ToolMessage(
        content=msg.content, 
        tool_call_id=msg.tool_call_id,
        name=msg.name
    ))
elif msg.tool_calls:
    ai_msg = AIMessage(content=msg.content, tool_calls=msg.tool_calls)
    formatted_msgs.append(ai_msg)
```

---

## Plano de Testes
1.  **Testar Persistência:** Criar teste unitário que salva uma mensagem com `tool_calls` e recupera, verificando integridade.
2.  **Testar Formatação:** Testar se `_format_history_as_messages` gera objetos `ToolMessage` corretamente.
3.  **Integration Test:** Simular conversa completa `User -> AI (Tool) -> Tool Result -> AI` e verificar se o prompt gerado tem a estrutura correta.

## Observação Importante
Devido à complexidade de migrar o histórico antigo (que não tem `tool_call_ids`), a nova lógica deve ser tolerante a falhas (fallback para o método antigo se não tiver ID).
