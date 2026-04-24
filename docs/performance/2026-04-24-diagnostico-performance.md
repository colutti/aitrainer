# Diagnostico de Performance - FityQ (2026-04-24)

## Contexto da execucao
- Escopo: diagnostico profundo com dados de producao e analise local de codigo.
- Projeto de producao: `fityq-488619`.
- Servicos principais analisados: `aitrainer-frontend`, `aitrainer-backend` (Cloud Run, `europe-southwest1`).
- Amostras usadas:
  - Backend requests: 234 entradas
  - Frontend requests: 300 entradas

## Evidencias coletadas

### 1) Infra/Cloud Run
- `aitrainer-backend`:
  - Limite: `cpu=1000m`, `memory=512Mi`, `concurrency=80`, `minScale=0`, `maxScale=20`
- `aitrainer-frontend`:
  - Limite: `cpu=1000m`, `memory=512Mi`, `concurrency=80`, `minScale=0`, `maxScale=20`
- O backend teve OOM no mesmo dia da coleta (24/04/2026):
  - `2026-04-24T06:41:21.021388Z`
  - `2026-04-24T17:42:36.457079Z`
  - `2026-04-24T17:55:56.468807Z`
  - `2026-04-24T20:26:00.853221Z`

### 2) Latencia agregada (Cloud Run requests)
- Backend (n=234):
  - `p50=0.059s`
  - `p95=9.560s`
  - `avg=1.524s`
- Frontend (n=300):
  - `p50=0.002s`
  - `p95=7.516s`
  - `avg=0.806s`

Interpretacao:
- A mediana e baixa, mas o p95 e muito alto em ambos, indicando cauda pesada (spikes) com impacto forte de percepcao de lentidao.

### 3) Endpoints de maior cauda (backend)
Tabela ordenada por p95:

| Path | n | p50 (s) | p95 (s) | media (s) |
|---|---:|---:|---:|---:|
| `/message` | 11 | 7.500 | 30.857 | 8.890 |
| `/user/login` | 3 | 5.972 | 11.568 | 6.316 |
| `/integrations/hevy/import` | 2 | 10.291 | 10.987 | 10.639 |
| `/user/public-config` | 4 | 9.675 | 10.312 | 7.426 |
| `/plan` | 9 | 0.046 | 9.266 | 1.173 |
| `/user/me` | 50 | 0.061 | 8.979 | 1.228 |
| `/message/history` | 10 | 4.008 | 8.648 | 3.709 |
| `/trainer/trainer_profile` | 10 | 3.752 | 7.969 | 3.238 |
| `/dashboard` | 6 | 0.351 | 3.975 | 0.949 |

Observacoes:
- `/message` e esperado ser pesado (LLM + tools), mas a variacao e extrema.
- Endpoints de bootstrap de tela (`/user/me`, `/message/history`, `/trainer/trainer_profile`) tambem aparecem com p95 alto.

### 4) Endpoints de maior cauda (frontend para backend via /api)
| Path | n | p50 (s) | p95 (s) | media (s) |
|---|---:|---:|---:|---:|
| `/api/message` | 10 | 7.516 | 11.361 | 6.756 |
| `/api/user/me` | 34 | 0.119 | 9.029 | 1.494 |
| `/api/message/history` | 6 | 4.451 | 8.712 | 3.961 |
| `/api/trainer/trainer_profile` | 6 | 3.991 | 8.020 | 3.498 |
| `/api/dashboard` | 2 | 0.416 | 4.023 | 2.220 |

### 5) Tráfego de probes/scan no frontend
- Aproximadamente `52.7%` da amostra do frontend sao requests tipo scan/probe (`*.php`, `xmlrpc.php`, `.git/config`, etc).
- Esses requests retornam `200` no frontend (comportamento comum de SPA fallback), consumindo capacidade da instância sem valor de produto.

## Analise de codigo local (causas provaveis)

### A) Chat frontend: digitação lenta
Arquivos principais:
- `frontend/src/features/chat/ChatPage.tsx`
- `frontend/src/features/chat/components/ChatView.tsx`
- `frontend/src/features/chat/components/MessageBubble.tsx`

Achados:
- `inputValue` fica no container (`ChatPage`) e muda a cada tecla.
- Cada tecla rerenderiza `ChatView` inteiro e faz novo `messages.map(...)`.
- Cada `MessageBubble` renderiza `ReactMarkdown` e `motion.div`.
- Resultado esperado: atraso perceptivel no teclado em historicos maiores (mesmo sem gargalo de API).

### B) Historico de chat no backend
Arquivo principal:
- `backend/src/repositories/chat_repository.py`

Achados:
- `get_history()` faz `find(SessionId)` sem paginacao no banco, le todas as mensagens da sessao, desserializa em Python e so depois filtra/pagina.
- Isso piora com crescimento de historico e afeta abertura de tela e "load more".

### C) Bootstrap de sessao e chamadas recorrentes
Arquivos principais:
- `frontend/src/shared/api/http-client.ts`
- `frontend/src/App.tsx`
- `frontend/src/shared/hooks/useAuth.ts`

Achados:
- `httpClient` adiciona `_t=Date.now()` em todo GET, anulando cache HTTP efetivamente.
- `App.tsx` recarrega `loadUserInfo()` no `window focus` quando autenticado.
- Em producao, `/user/me` aparece muito frequente e com cauda alta relevante.

### D) Bundle inicial do frontend
Build local principal:
- JS principal: `~1.68 MB` minificado (`~488 KB gzip`)
- CSS principal: `~125 KB` (`~18.7 KB gzip`)

Achado:
- Bundle principal grande para app com varias telas, aumenta tempo de parse/exec inicial e piora UX em dispositivos mais fracos.

## Ranking de gargalos (impacto x confianca)
1. Infra backend (OOM + cauda de latencia alta em endpoints base)
- Impacto: muito alto
- Confianca: alta

2. Fluxo de chat (render no frontend + historico caro no backend)
- Impacto: muito alto
- Confianca: alta

3. Bootstrap/session refresh (`/user/me` com alta frequencia + sem cache)
- Impacto: alto
- Confianca: media-alta

4. Bundle inicial grande no frontend
- Impacto: medio-alto
- Confianca: media

5. Trafego de scan/probe atingindo frontend/backend
- Impacto: medio (capacidade desperdicada e ruido de latencia)
- Confianca: alta

## Lacunas de observabilidade
- Falta log estruturado de duracao por etapa interna no backend (DB, prompt build, LLM, persistencia).
- Falta metricas de web-vitals e tempos de tela no frontend em producao.
- Sem correlacao request_id full-stack para juntar request web + etapas backend.

## Conclusao executiva
- A lentidao geral percebida e real e sustentada por dados de producao (p95 muito alto).
- O problema nao esta em uma camada unica: ha contribuicao de infra (OOM), backend (cauda em endpoints base), frontend (chat render e bundle), e ruido operacional (scan traffic).
- O chat, mesmo fora de foco desta rodada, ja tem causa tecnica forte para o delay de digitacao.

## Proximas acoes recomendadas (fase de remediacao)
1. Estabilizar infra backend para remover OOM da equacao (memoria/concurrency/min instances) e re-medicao.
2. Instrumentar backend com tempos por etapa para separar gargalo de DB vs LLM vs serializacao.
3. Corrigir arquitetura de render do chat (isolar input de lista de mensagens, memoizacao efetiva dos bubbles, reduzir custo de markdown por tecla).
4. Reprojetar leitura de historico no backend para paginacao no banco (evitar full scan + desserializacao completa).
5. Revisar estrategia de fetch de `/user/me` e cache busting global de GET.
6. Reduzir ruido de scan/probe (WAF/rules/rate-limits no edge) para proteger capacidade.

