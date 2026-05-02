# SessionContextNode

Role:
- Hydratador deterministico de dados do turno.

Objective:
- Carregar perfil do usuario e do treinador, agenda, metabolismo, historico e plano ativo.
- Produzir runtime_context_json e sinais de lifecycle do plano.
- Nao fazer inferencia por LLM; todo trabalho e feito em codigo.

Allowed context:
- Request, user profile, agenda, active plan, metabolism e history summary.

Core behavior:
- Hydratar perfil, trainer_profile, metabolismo, plano, eventos ativos e historico da janela de memoria.
- Derivar sinais objetivos de lifecycle do plano: timeline_expired, next_review_due.
- Preencher runtime_context_json com session channel e response_locale.
- Nao produzir texto para usuario; marcar output como "hydrated".

Tool policy:
- Nenhum uso de tool neste no.

Output contract:
- Nenhuma resposta LLM. Apenas marcar `state.node_outputs["session_context"] = "hydrated"`.