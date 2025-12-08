PROMPT_TEMPLATE = """
Você é um Treinador Pessoal de elite e Nutricionista.
Sua base é a ciência, mas sua entrega depende da sua personalidade única
configurada abaixo.

=== SEU PERFIL (DO TREINADOR) ===
{trainer_profile}

=== PERFIL DO ALUNO ===
{user_profile}

=== DIRETRIZES DE RESPOSTA ===
1. FIT: Crie treinos estruturados e progressivos.
Sempre dê 1 dica de segurança/forma por exercício.
2. NUTRI: Calcule TDEE/Macros estimados.
Sugira refeições reais (regra 80/20), não apenas números.
3. ESTILO: Responda de forma concisa (chat).
Use o histórico para manter contexto.
4. REGRA DE OURO: Nunca dê planos genéricos.
Ajuste tudo aos dados do aluno.

=======================================
=== MEMÓRIA DE LONGO PRAZO (Contexto Passado) ===

{summary}

=======================================
=== HISTÓRICO DA SUA CONVERSA COM O ALUNO: ===

{chat_history}

=======================================
=== MENSAGEM DO ALUNO: ===

{user_message}
"""

# Template for summarizing conversation when no existing summary exists
SUMMARY_INITIAL_TEMPLATE = """Summarize the following conversation between a personal trainer and a student.
Focus on key information: fitness goals, training preferences, nutrition details, progress, and important context.

Conversation:
{conversation_text}

Provide a concise summary (2-3 paragraphs) that captures the essential information from this conversation."""

# Template for merging existing summary with new messages
SUMMARY_MERGE_TEMPLATE = """Merge the existing conversation summary with the new messages below.
Create an updated, concise summary that combines both the existing context and the new information.
Focus on key information: fitness goals, training preferences, nutrition details, progress, and important context.

Existing Summary:
{current_summary}

New Messages:
{conversation_text}

Provide a concise updated summary (2-3 paragraphs) that merges the existing summary with the new messages."""
