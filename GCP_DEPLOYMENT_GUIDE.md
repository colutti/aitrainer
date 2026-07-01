# GCP Deployment Guide

Este documento descreve apenas o fluxo de deploy atualmente suportado pelo repositório.

## Produção atual

- Domínio principal: `https://fityq.com`
- Deploy compute: Google Cloud Run
- Região padrão: `europe-southwest1`
- Registry padrão: `europe-southwest1-docker.pkg.dev/fityq-488619/aitrainer`

Serviços Cloud Run padrão:

- `aitrainer-backend`
- `aitrainer-frontend`

Serviços admin existem, mas o deploy deles é opt-in via `ENABLE_ADMIN_DEPLOY=true`.

## Fluxo oficial

O fluxo oficial de deploy é:

```bash
make deploy-prod
```

Esse fluxo encadeia:

1. `make deploy-preflight`
2. `make deploy-build`
3. `scripts/deploy/deploy_prod.sh`
4. `make deploy-smoke`

Comandos auxiliares:

```bash
make deploy-prod-fast
make deploy-build
make deploy-smoke
make deploy-prod-env
```

## Garantias do fluxo

- O deploy principal usa `gcloud run services update --image`, preservando env vars já existentes no serviço.
- O preflight valida dependências locais, existência dos serviços Cloud Run e env vars críticas.
- O smoke testa:
  - `${BACKEND_URL}/health`
  - `${FRONTEND_URL}/api/health`
  - `${FRONTEND_URL}/runtime-config.js`

## Variáveis relevantes

Os scripts de deploy usam estes defaults:

- `GCP_PROJECT_ID=fityq-488619`
- `GCP_REGION=europe-southwest1`
- `AR_REPOSITORY=aitrainer`
- `ENABLE_ADMIN_DEPLOY=false`
- `DRY_RUN=false`

Variáveis opcionais de controle:

- `DEPLOY_TAG`
- `AUTO_DETECT_CHANGED=true`
- `BASE_REF=<git-ref>`

## Atualização de env vars

Para sincronizar env vars de produção a partir dos arquivos locais `*.env.prod`:

```bash
make deploy-prod-env
```

Arquivos lidos:

- `backend/.env.prod`
- `frontend/.env.prod`
- `backend-admin/.env.prod` quando `ENABLE_ADMIN_DEPLOY=true`
- `frontend/admin/.env.prod` quando `ENABLE_ADMIN_DEPLOY=true`

## Descoberta de URLs atuais

Evite documentar URLs temporárias de Cloud Run manualmente. Consulte o estado atual com:

```bash
gcloud run services describe aitrainer-backend --region europe-southwest1 --format='value(status.url)'
gcloud run services describe aitrainer-frontend --region europe-southwest1 --format='value(status.url)'
```

## Telegram webhook

O bot do Telegram usa webhook. Após um deploy de backend que altere a URL efetiva do serviço, confirme que o webhook aponta para:

```text
<backend-url>/telegram/webhook
```
