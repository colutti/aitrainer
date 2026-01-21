
SUMMARY_UPDATE_PROMPT = """
Você é um assistente especialista em sumarização de contexto de longo prazo.

<current_summary>
{current_summary}
</current_summary>

<new_lines>
{new_lines}
</new_lines>

SUA TAREFA:
Atualize o "Resumo Atual" incorporando as informações relevantes das "Novas Linhas".

REGRAS RÍGIDAS:
1. Mantenha o resumo CONCISO.
2. PRESERVE DATAS importantes (lesões,recordes, mudanças de peso).
3. Ignore saudações ("oi", "tchau") e conversas triviais.
4. Se o "Resumo Atual" estiver vazio, crie um novo baseado apenas nas novas linhas.
5. O resultado deve ser um texto corrido ou em tópicos, pronto para ser injetado no System Prompt de um Treinador AI.
6. Use PORTUGUÊS.

NOVO RESUMO ATUALIZADO:
"""
