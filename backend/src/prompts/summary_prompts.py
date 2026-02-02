"""
Summarization prompts for progressively building long-term memory summaries.

Two prompts:
1. SUMMARY_PROMPT: Legacy (for ConversationSummaryBufferMemory if needed)
2. SUMMARY_UPDATE_PROMPT: Current V3 - Updates existing summary with new info, generates JSON structure
"""

# ===== LEGACY PROMPT (Kept for compatibility) =====
SUMMARY_PROMPT = """
Resuma a conversa progressivamente, MAS PRESERVE EXATAMENTE:
1. Últimos PRs (cargas e repetições)
2. Mudanças de dieta ou peso (datas e valores)
3. Lesões ou dores relatadas

Não transforme "supino 80kg" em "fez exercícios de peito".
Mantenha os números. Descarte saudações e conversas triviais.
"""

# ===== CURRENT V4 PROMPT - Inspired by ChatGPT/Mem0 =====
SUMMARY_UPDATE_PROMPT = """Você é um Personal Information Organizer especializado em fitness.
Sua tarefa: extrair FATOS ATÔMICOS das mensagens do ALUNO e atualizar o perfil.

<current_profile>
{current_summary}
</current_profile>

<new_conversation>
{new_lines}
</new_conversation>

## REGRAS DE EXTRAÇÃO

### EXTRAIR (fatos duradouros do ALUNO):
- Preferências: horários, frequência, equipamentos, exercícios favoritos
- Limitações: lesões, dores, restrições médicas, alergias
- Objetivos: metas declaradas pelo aluno
- Decisões: escolhas confirmadas ("vou fazer 2x/sem", "prefiro máquinas")

### IGNORAR (não são fatos do aluno):
- Logs de sistema: "executado", "retornou X registros"
- Saudações: "oi", "tchau", "ok"
- Dados numéricos brutos: pesos diários, calorias, macros (recuperáveis do DB)

## FORMATO DE CADA FATO

"[DD/MM] descrição concisa do fato"

Exemplos CORRETOS:
- "[31/01] Prefere treinar Push 2x/semana"
- "[15/01] Lesão no joelho esquerdo - evitar agachamento profundo"
- "[01/02] Meta: perder 0.25kg/semana"

Exemplos INCORRETOS:
- "Prefere treinar 2x/sem" (SEM DATA)
- "update_hevy_routine executado" (LOG DE SISTEMA)

## SUBSTITUIÇÃO AUTOMÁTICA

Se um fato novo CONTRADIZ um existente na mesma categoria:
- REMOVA o antigo
- MANTENHA apenas o novo

Exemplo:
- Perfil tem: "[25/01] Push 1x/semana"
- Aluno diz: "Mudei, vou fazer 2x"
- Resultado: manter APENAS "[31/01] Push 2x/semana"

## CATEGORIAS (JSON)

{{
  "health": [],      // lesões, condições médicas, alergias
  "goals": [],       // objetivos declarados, metas
  "preferences": [], // preferências de treino, horários, equipamentos
  "progress": [],    // PRs, marcos importantes
  "restrictions": [] // restrições absolutas, limitações permanentes
}}

## EXEMPLOS

### Input 1:
Aluno: "Vou fazer o treino de Push duas vezes por semana"

### Output 1:
{{"preferences": ["[31/01] Treino Push 2x/semana"]}}

### Input 2 (ruído - retornar vazio):
Sistema: list_hevy_routines executado
Treinador: "Sua rotina foi atualizada"

### Output 2:
{{}}

### Input 3 (substituição):
Perfil atual: {{"preferences": ["[25/01] Push 1x/semana"]}}
Aluno: "Mudei de ideia, vou fazer 2x por semana"

### Output 3:
{{"preferences": ["[31/01] Push 2x/semana"]}}

## OUTPUT

Retorne APENAS JSON válido. Sem markdown, sem explicações.
Se nenhum fato novo relevante: retorne {{}}
"""

# ===== MEM0 FACT EXTRACTION PROMPT =====
MEM0_FACT_EXTRACTION_PROMPT = """
Extraia fatos memoráveis da conversa abaixo. Retorne um JSON com "facts" array.

EXTRAIA (Persistem como memória):
- Training preferences: horários, tipos de exercício, equipamentos
- Physical limitations: lesões, dores, restrições médicas
- Health conditions: alergias, diabetes, limitações
- Qualitative goals: ambições, motivações
- Schedule: disponibilidade, turno de trabalho
- Equipment: que equipamento tem disponível
- Food preferences: vegetariano, intolerâncias, preferências

NÃO EXTRAIA (Dados recuperáveis):
- Weight: "85.2kg"
- Calories: "2500 cal"
- Workout details: "4x10 squats at 80kg"
- Macro numbers: "180g protein"
- Daily nutrition logs

JSON Output format:
{{"facts": ["fato1", "fato2", ...]}}

Retorne APENAS o JSON válido.
"""
