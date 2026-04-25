# 🚀 AI Trainer - Guia de Infraestrutura e Deployment (GCP)

Este documento descreve a arquitetura atualizada, os serviços utilizados e como manter a aplicação no Google Cloud Platform (GCP).

## 🌍 URLs de Produção

| Serviço                | URL                                                                                                                                                | Status                       |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------- |
| **Frontend Principal** | [https://fityq.com](https://fityq.com)                                                                                                             | Ativo (via Firebase Hosting) |
| **Backend API**        | [https://aitrainer-backend-ufyggn7wzq-no.a.run.app](https://aitrainer-backend-ufyggn7wzq-no.a.run.app)                                             | Ativo (Cloud Run)            |
| **Admin Frontend**     | [https://aitrainer-frontend-admin-359890746855.europe-southwest1.run.app](https://aitrainer-frontend-admin-359890746855.europe-southwest1.run.app) | Ativo (Cloud Run)            |
| **Admin Backend**      | [https://aitrainer-backend-admin-359890746855.europe-southwest1.run.app](https://aitrainer-backend-admin-359890746855.europe-southwest1.run.app)   | Ativo (Cloud Run)            |

> [!NOTE]
> O bot do Telegram utiliza webhooks. Após o deploy do backend, o webhook deve ser atualizado para a URL do Cloud Run (terminada em `/telegram/webhook`).


---

## 🏗️ Arquitetura no GCP

A aplicação foi migrada do Render para o Google Cloud para maior controle, performance (Madrid) e redução de custos.

1.  **Google Cloud Run (Compute):**
    *   Hospeda os containers de Backend, Admin Backend e Admin Frontend.
    *   Região: `europe-southwest1` (Madrid).
    *   Configurado com auto-scaling (paga apenas pelo que usa).
2.  **Firebase Hosting (Custom Domain Proxy):**
    *   Utilizado para mapear o domínio `fityq.com` para o Cloud Run de Madrid.
    *   Provê SSL (HTTPS) gratuito e CDN global.
3.  **Artifact Registry:**
    *   Repositório: `europe-southwest1-docker.pkg.dev/fityq-488619/aitrainer/`
    *   Armazena as imagens de container compiladas.

---

## 🚀 Como Realizar um Novo Deployment

O fluxo oficial de produção agora é **one-shot** e orientado a cache remoto para reduzir tempo de build/deploy.

### Comandos oficiais

| Comando             | Descrição |
| :------------------ | :-------- |
| `make deploy-prod`  | Fluxo completo: preflight + build com cache + deploy + smoke |
| `make deploy-prod-fast` | Fluxo incremental: só build/deploy de serviços alterados |
| `make deploy-build` | Build-only via Cloud Build/Kaniko com cache remoto |
| `make deploy-smoke` | Smoke-only após deploy |
| `make deploy-prod-env` | Sincroniza env vars de produção a partir de arquivos `*.env.prod` |

**Exemplo de uso (recomendado):**
```bash
make deploy-prod
```

### Garantia contra perda de env vars

- O deploy principal usa `gcloud run services update --image`, que atualiza somente a imagem e preserva variáveis existentes.
- O preflight valida chaves críticas para social auth e backend antes do deploy.
- O smoke valida `/health`, proxy frontend `/api/health` e `runtime-config.js` com chaves Firebase não vazias.

> [!IMPORTANT]
> Não colocar segredos diretamente no `Makefile`. Quando necessário, atualizar `backend/.env.prod` e executar `make deploy-prod-env`.

---

## ⚙️ Variáveis de Ambiente e IA

Os modelos de IA configurados e testados são:
*   **AI_PROVIDER:** `gemini`
*   **GEMINI_LLM_MODEL:** `gemini-3-flash-preview`
*   **GEMINI_EMBEDDER_MODEL:** `gemini-embedding-001`
*   **OPENAI_LLM_MODEL:** `gpt-5-mini`
*   **OPENAI_EMBEDDER_MODEL:** `text-embedding-3-small`

As variáveis são geridas pelos scripts em `scripts/deploy/`. Para atualização explícita a partir de arquivo, use `make deploy-prod-env`.

---

## 💻 Desenvolvimento Local (Podman/Docker)

As mudanças para o GCP **não impactaram** o ambiente local. Você ainda pode rodar tudo via:

```bash
podman-compose up --build
```

*   **Frontend Local:** [http://localhost:3000](http://localhost:3000)
*   **Backend Local:** [http://localhost:8000](http://localhost:8000)
*   **Banco de Dados:** MongoDB e Qdrant rodam em containers locais.
