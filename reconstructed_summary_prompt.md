# Prompt de Sumarização (History Compactor) - Reconstruído

**Data/Hora:** 2026-01-23 18:46:35 UTC
**Usuário:** rafacolucci@gmail.com
**Tipo:** Sumarização (Simple Prompt)

---

## 🖥️ Prompt Enviado

Você é um assistente especialista em sumarização de contexto de longo prazo.

<current_summary>
Resumo atualizado (conciso, pronto para System Prompt)

- Perfil e objetivo (meta registrada pelo sistema em 23/01): masculino, 45 anos, 1,75 m, peso inicial 80,0 kg; objetivo atual = perder 0,4 kg/sem. (Meta operacional salva anteriormente para recomposição = 2.050 kcal/dia; alguns relatórios usaram 2.000 kcal — atenção à fonte do alvo.)

- Peso & composição (datas importantes)
  - 09/12/2025: 77,70 kg (BIA 55,40% músculo).
  - 06/01/2026: 76,80 kg.
  - 12/01/2026: 76,85 kg.
  - 18/01/2026: 75,45 kg.
  - 21/01/2026: 76,50 kg.
  - Tendência recente: perda rápida entre 06→18/01 (~−1,35 kg em 12 dias); média móvel 7 dias ≈ 76,7 kg. Pesagem padronizada manhã/jejum.

- Treino & performance (datas importantes)
  - Sistema encontrou 10 treinos registrados (get_workouts executado em 23/01 — 10 treinos).
  - 23/01/2026 — Push (62 min): Supino Inclinado na máquina 3x7 @60 kg; Supino Sentado (máquina) 8@62,5 / 7@62,5 / 7@62,5; Prensa de Ombros (sentada).
  - Força em progresso geral (ex.: Leg Press até 270 kg em 21/01; pull‑ups 1º conjunto 4 reps sem assistência).

- Eventos nutricionais e padrão de compensação (datas)
  - 19/01: ~2.095 kcal (registrado).
  - 20/01: 2.040 kcal (P 176 g, C 236 g, G 47 g).
  - 22/01: 1.513 kcal (P 133 g, C 148 g, G 42 g, Fibras 36 g, Sódio 264 mg). Usuário relatou ter reduzido ingestão em 22/01 para “compensar” excesso anterior.
  - Padrão detectado: episódios de ingestão mais alta seguidos por déficit compensatório (não ideal para preservação de massa magra se mantido).

- Estimativas energéticas e metas (atualizado 23/01)
  - BMR (Mifflin‑St Jeor) calculado em 23/01: 1.674 kcal/dia.
  - Dois métodos divergentes apresentados:
    - AF ≈1,55 → TDEE ≈2.595 kcal/dia (~2.600 kcal). Para −0,4 kg/sem deficit ≈570 kcal/dia.
    - Sedentário + custo médio do treino → TDEE ≈2.283 kcal/dia (faixa ≈2.250–2.350 kcal; intermediário ≈2.300 kcal). Usuário passa o dia sentado → 2.600 pode ser alto.
  - Pergunta operacional (23/01): fixar manutenção em ≈2.600 kcal, ≈2.300 kcal, ou calcular gasto exato das sessões usando os dados dos treinos — usuário optou por calcular gasto das sessões.

- Ação técnica executada / integrações (23/01)
  - Tool 'get_workouts' executada com sucesso (23/01): encontrou 10 treinos.
  - Sistema sugere calcular o gasto exato das sessões usando dados de duração/intensidade para devolver um TDEE médio.
  - Tentativa de atualizar rotina ("update_hevy_routine") falhou ao enviar atualização para o Hevy ao atualizar a rotina "Pull" — provável problema de integração (API key inválida/conexão negada) ou payload incompatível.
  - Opções propostas: (1) tentar novamente (risco de nova falha), (2) enviar rotina "Pull" completa para colagem manual no Hevy (recomendado), (3) guiar o usuário a validar/ativar a API key nas configurações para solução definitiva.

- Nutrição — padrões e recomendações práticas (mantidas / reforçadas)
  - Médias recentes: calorias ≈1.986 kcal/dia; proteína historicamente alta (≈190–204 g/dia) mas com quedas recentes; carboidratos frequentemente baixos para volume de treino; fibra frequentemente abaixo do alvo.
  - Macros otimizadas propostas: proteína 1,8–2,0 g/kg (≈144–160 g/dia); gorduras 25–30% (≈72–88 g/dia); carboidratos = calorias restantes.
  - Risco atual: dias com proteína insuficiente (ex.: 22/01) e déficits compensatórios podem aumentar risco de perda de massa magra.
  - Ação prática sugerida: evitar déficits compensatórios; lanche pós‑treino prático (whey ou iogurte grego + aveia + fruta); manter creatina diária.

- NEAT & passos
  - NEAT estimado: ~7.000 passos/dia → gasto adicional ≈250–400 kcal; assistente ajusta saldo quando contabiliza treino + steps.

- Monitorização e próximos passos acordados
  - Limiares de alerta: perda >0,6 kg/sem, ganho >0,4 kg/sem, ou queda consistente de massa BIA + perda de força.
  - Decisões pendentes: confirmar manutenção a adotar (≈2.600 vs ≈2.300) ou autorizar cálculo detalhado do gasto das sessões (sistema sugeriu estimar por duração/intensidade para produzir TDEE médio). Recomendações: enviar rotina manualmente ou validar API key para completar cálculo/atualização.
</current_summary>

<new_lines>
[23/01 17:37] Sistema: Procedimento e premissas rápidas (transparência de sistema): usei o método MET para resistência. Fórmula: kcal/min = MET × 3,5 × peso(kg) / 200. Peso = 80 kg → fator = 1,4 kcal/min por MET. Classifiquei cada sessão por intensidade (METs) com base em duração, predominância de grandes grupos e volume/loads registrados. Se quiser, refaço com METs ajustados ao seu feeling de esforço.

| Data / Treino | Duração (min) | MET usado | Gasto estimado (kcal) |
|---|---:|---:|---:|
| 23/01 — Push | 62 | 5.5 | 477 |
| 21/01 — Legs | 55 | 6.5 | 501 |
| 20/01 — Pull | 63 | 5.5 | 485 |
| 19/01 — Push | 72 | 5.8 | 585 |
| 17/01 — Full‑Body A | 84 | 6.8 | 800 |
| 14/01 — Pull | 60 | 5.5 | 462 |
| 13/01 — Legs | 45 | 6.0 | 378 |
| 12/01 — Push | 66 | 5.5 | 508 |
| 02/01 — Pull | 75 | 6.0 | 630 |
| 31/12 — Legs | 64 | 6.5 | 582 |

Média por sessão (essas 10): ≈ 541 kcal/sessão. Assumindo frequência média 4,5 sessões/semana (você indicou 4–5×/sem), o gasto de treino médio diário = (541 × 4,5) / 7 ≈ 348 kcal/dia. BMR (Mifflin) = 1.674 kcal → linha base sedentário (BMR×1,20) = ≈2.009 kcal/dia. Somando o custo médio diário do treino → TDEE médio ≈ 2.009 + 348 ≈ 2.357 kcal/dia (arredondado ≈ 2.350 kcal).

Interpretação operacional: esse TDEE está entre as estimativas anteriores (2.300–2.600). Se quiser precisão maior eu: (A) recalculo usando outra suposição de METs por sessão (você pode confirmar RPE de cada treino), ou (B) uso sua frequência real dos últimos 4 semanas em vez de 4,5 sess/sem. Quer que eu fixe ~2.350 kcal como sua manutenção prática ou recalculamos com ajustes?
[23/01 17:38] Sistema: ✅ Tool 'get_workouts' executed. Result: Encontrei 50 treino(s):

1. [Push] 23/01/2026 11:45 (62min)
   Exercícios: 3x7 Supino Inclinado Na Máquina @ 60.0kg; Supino Sentado (Máquina): 8@62.5kg, 7@62.5kg, 7@62.5kg; Prensa De Ombros (Sentada) 
[23/01 17:39] Sistema: frequência real dos últimos 4 semanas em vez de 4,5 sess/sem
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
