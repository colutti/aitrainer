# Deploy em Produção (Cloud Run)

## Objetivo
Padronizar deployment rápido e previsível com cache remoto de imagens e sem perda de variáveis de ambiente.

## Pré-requisitos
- `gcloud` autenticado no projeto correto
- Permissão para Cloud Build, Artifact Registry e Cloud Run

## Fluxo one-shot recomendado
```bash
make deploy-prod
```

Esse comando executa:
1. `make deploy-preflight`: valida comandos, serviços e variáveis críticas (incluindo Firebase social auth).
2. `make deploy-build`: build paralelo das imagens via Cloud Build + Kaniko com cache remoto.
3. `scripts/deploy/deploy_prod.sh`: atualiza imagens no Cloud Run sem limpar env vars.
4. `make deploy-smoke`: valida `/health`, proxy `/api/health` e `runtime-config.js` com chaves Firebase não vazias.

## Fluxo rápido (change-aware)
Para deploys incrementais, evitando build/deploy de serviço não alterado:
```bash
make deploy-prod-fast
```

Variáveis úteis:
- `AUTO_DETECT_CHANGED=true` ativa detecção por diff git.
- `BASE_REF=<ref>` define base do diff (default: `HEAD~1`).

## Sincronizar env vars de produção
Se precisar atualizar vars no Cloud Run a partir de arquivos locais `*.env.prod`:
```bash
make deploy-prod-env
```

Arquivos padrão usados:
- `backend/.env.prod` -> `aitrainer-backend`
- `frontend/.env.prod` -> `aitrainer-frontend` (opcional)
- Quando `ENABLE_ADMIN_DEPLOY=true`, também usa `backend-admin/.env.prod` e `frontend/admin/.env.prod`.

## Variáveis de controle
- `GCP_PROJECT_ID` (default: `fityq-488619`)
- `GCP_REGION` (default: `europe-southwest1`)
- `AR_REPOSITORY` (default: `aitrainer`)
- `DEPLOY_TAG` (opcional)
- `ENABLE_ADMIN_DEPLOY=true` para incluir serviços admin
- `DRY_RUN=true` para simulação sem mudanças
- `AUTO_DETECT_CHANGED=true` para build/deploy apenas de serviços alterados
- `BASE_REF` para controlar comparação de mudanças no modo change-aware

## Medição de tempo
- Tempo de build total é mostrado por `build_images.sh`.
- Tempo de deploy/smoke é mostrado ao final dos scripts.
- Artefatos de execução local:
  - `scripts/deploy/.last_build.env`
  - `scripts/deploy/.last_deploy.env`
