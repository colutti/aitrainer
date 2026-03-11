"""
Constantes reutilizáveis para prompts do sistema.

Centraliza strings comuns que aparecem em múltiplos prompts,
facilitando ajustes globais sem editar templates individuais.
"""

# ===== REGRAS GERAIS =====
SCOPE_RULE = "Escopo: saúde/fitness/nutrição apenas."
SIZE_RULE = "3-4 parágrafos (~100-150 palavras), exceto se pedir plano detalhado."
STRUCTURE_RULE = "Prosa natural, não excesso de bullets. Varie estrutura."
TABLE_RULE = "Tabelas em GFM. Nunca mostre IDs internos."

# ===== FERRAMENTAS =====
TOOLS_CAN_SAVE = "✅ SALVE: treino, nutrição, composição corporal"
TOOLS_CANNOT_SAVE = "❌ NÃO SALVE: descanso, água, humor, sono"

# ===== DATAS =====
DATE_FORMAT_RULE = "Datas em YYYY-MM-DD (use data atual para referência: se 'dia X', use mês/ano atuais)."

# ===== MEMÓRIAS =====
MEMORY_CRITICAL = "[CRÍTICO]"
MEMORY_SEMANTIC = "[RELACIONADO]"
MEMORY_RECENT = "[RECENTE]"
MEMORY_NONE = "Nenhum conhecimento prévio relevante encontrado."

# ===== SEÇÕES =====
SECTION_PROFILE = "## Perfil do Usuário"
SECTION_TOOLS = "## Ferramentas Disponíveis"
SECTION_CONTEXT = "## Contexto"

# ===== SUMMARIZAÇÃO =====
SUMMARY_PRESERVE = ["datas", "números", "preferências", "restrições", "metas"]
SUMMARY_DISCARD = ["saudações", "conversas triviais", "clima", "humor"]
