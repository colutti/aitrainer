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

# ===== CURRENT V3 PROMPT - JSON STRUCTURED =====
SUMMARY_UPDATE_PROMPT = """
Você é um assistente especialista em sumarização estruturada de contexto de longo prazo.

<current_summary>
{current_summary}
</current_summary>

<new_lines>
{new_lines}
</new_lines>

SUA TAREFA:
Atualize o resumo incorporando as informações relevantes das novas linhas.
Retorne um JSON estruturado (NÃO texto livre) com as categorias abaixo.

CATEGORIAS ESTRUTURADAS:
- health: lesões, alergias, restrições médicas, limitações físicas
- goals: objetivos de fitness (ganhar massa, perder peso, performance)
- preferences: preferências de treino (horários, equipamentos, tipos de exercício)
- progress: progressão em exercícios (cargas, tempos, recordes)
- restrictions: restrições absolutas (não pode agachar, operação, etc)

REGRAS RÍGIDAS (CRÍTICO):
1. Retorne APENAS um JSON válido, nada de markdown ou explicações.
2. PRESERVE DATAS e NÚMEROS especiais (datas de lesões, cargas em kg, tempos, calorias).
3. Use listas dentro de cada categoria: ["item1", "item2"]
4. Se categoria está vazia, omita da resposta ou use lista vazia [].
5. NUNCA descarte: health e restrictions (são protegidas).
6. Ignore saudações triviais ("oi", "tchau", comentários sobre clima/humor).
7. Use PORTUGUÊS em todos os itens.

EXEMPLO DE OUTPUT ESPERADO:
{{
  "health": ["lesão joelho desde 15/01/2026", "alergia a lactose"],
  "goals": ["ganhar 5kg de massa muscular", "correr 10km sem parar"],
  "preferences": ["treina de manhã", "prefere máquinas a barra"],
  "progress": ["agachamento: 60kg (jan) → 80kg (fev)", "supino: sem progresso"],
  "restrictions": ["não pode agachar profundo"]
}}

IMPORTANTE: Retorne APENAS o JSON, sem nenhum texto antes ou depois.
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
