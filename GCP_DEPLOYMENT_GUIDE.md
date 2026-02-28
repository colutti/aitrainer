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

O processo foi integrado e organizado no **Makefile** da raiz do projeto. Ele utiliza o arquivo `backend/.env.prod` para injetar segredos de forma segura (sem expô-los em scripts ou no Makefile).

### Comandos de Deployment:

| Comando           | Descrição                                                                 |
| :---------------- | :------------------------------------------------------------------------ |
| `make gcp-full`   | **Executa o fluxo completo**: Build + Push + Deploy de todos os serviços. |
| `make gcp-build`  | Apenas compila as imagens locais usando Podman.                           |
| `make gcp-push`   | Envia as imagens para o Artifact Registry no GCP.                         |
| `make gcp-deploy` | Atualiza os serviços no Cloud Run injetando o `.env.prod`.                |
| `make gcp-list`   | Lista o status e as URLs dos serviços ativos no Cloud Run.                |

**Exemplo de uso:**
```bash
make gcp-full
```

> [!IMPORTANT]
> Nunca adicione chaves ou senhas diretamente no `Makefile`. Sempre edite o arquivo [backend/.env.prod](file:///home/colutti/projects/personal/backend/.env.prod) caso precise mudar alguma configuração de produção.

---

## ⚙️ Variáveis de Ambiente e IA

Os modelos de IA configurados e testados são:
*   **AI_PROVIDER:** `gemini`
*   **GEMINI_LLM_MODEL:** `gemini-3-flash-preview`
*   **GEMINI_EMBEDDER_MODEL:** `gemini-embedding-001`
*   **OPENAI_LLM_MODEL:** `gpt-5-mini`
*   **OPENAI_EMBEDDER_MODEL:** `text-embedding-3-small`

As variáveis são injetadas durante o deploy. Se precisar alterar alguma, edite o arquivo `scripts/deploy-cloudrun.sh`.

---

## 💻 Desenvolvimento Local (Podman/Docker)

As mudanças para o GCP **não impactaram** o ambiente local. Você ainda pode rodar tudo via:

```bash
podman-compose up --build
```

*   **Frontend Local:** [http://localhost:3000](http://localhost:3000)
*   **Backend Local:** [http://localhost:8000](http://localhost:8000)
*   **Banco de Dados:** MongoDB e Qdrant rodam em containers locais.

