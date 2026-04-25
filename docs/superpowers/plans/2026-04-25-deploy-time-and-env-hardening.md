# Deploy Time and Env Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduzir o tempo de deploy de frontend/backend para abaixo de 8 minutos no fluxo padrão e impedir perda de variáveis de ambiente em produção.

**Architecture:** Separar build/verify de image build, habilitar cache remoto determinístico no build de containers, e padronizar deploy Cloud Run com atualização de imagem sem sobrescrever env vars. Criar uma trilha única de publicação (`make deploy-prod`) com pré-checks e smoke test automatizado. Registrar o procedimento final em documentação única e atualizada.

**Tech Stack:** Cloud Run, Artifact Registry, Docker Buildx, GitHub Actions, Makefile, Bash, FastAPI, React/Vite, Nginx.

---

## File Structure

- Modify: `backend/Dockerfile`
  Purpose: remover verificações pesadas do caminho de build de produção e manter imagem runtime enxuta.
- Modify: `backend-admin/Dockerfile`
  Purpose: mesmo ajuste de performance para admin backend.
- Modify: `frontend/Dockerfile`
  Purpose: evitar etapas redundantes no build de imagem de produção e otimizar camadas de cache.
- Modify: `frontend/admin/Dockerfile`
  Purpose: remover instalação duplicada de dependências e reduzir contexto de build.
- Create: `scripts/deploy/deploy_prod.sh`
  Purpose: script único de deploy em produção com estratégia que preserva env vars existentes do Cloud Run.
- Create: `scripts/deploy/preflight.sh`
  Purpose: validar credenciais, projeto/região, existência de serviços e env vars obrigatórias antes do deploy.
- Create: `scripts/deploy/smoke_test.sh`
  Purpose: validar health endpoints e autenticação social pós deploy.
- Create: `scripts/deploy/README.md`
  Purpose: documentar variáveis, fluxo e troubleshooting rápido dos scripts.
- Modify: `Makefile`
  Purpose: expor targets oficiais `deploy-prod`, `deploy-prod-fast`, `deploy-preflight`, `deploy-smoke`.
- Create: `.github/workflows/deploy-prod.yml`
  Purpose: pipeline manual (`workflow_dispatch`) com builds paralelos e cache remoto no Artifact Registry.
- Modify: `README.md`
  Purpose: adicionar seção oficial de deploy container-first.
- Modify: `GCP_DEPLOYMENT_GUIDE.md`
  Purpose: substituir instruções desatualizadas por processo real e anti-regressão de env vars.
- Create: `docs/deploy/production-deploy-runbook.md`
  Purpose: runbook operacional único para quando você pedir “faça deploy”.
- Create: `docs/deploy/deploy-benchmark.md`
  Purpose: baseline e comparação de tempos (antes/depois) com evidência.
- Test: `scripts/deploy/tests/test_preflight.sh` (opcional se padrão existente permitir testes shell)
  Purpose: garantir validação de pré-condições críticas.

### Task 1: Baseline de tempo e gargalos reais

**Files:**
- Create: `docs/deploy/deploy-benchmark.md`
- Modify: `docs/deploy/production-deploy-runbook.md` (criar se não existir)

- [ ] **Step 1: Coletar baseline de tempo atual (build+push+deploy)**

Run:
```bash
cd /home/colutti/projects/personal
export GCP_PROJECT_ID=fityq-488619
export GCP_REGION=europe-southwest1
export REPO=europe-southwest1-docker.pkg.dev/${GCP_PROJECT_ID}/aitrainer
export SHA=$(git rev-parse --short HEAD)

/usr/bin/time -p bash -lc '
  docker build -t ${REPO}/backend:${SHA}-baseline ./backend &&
  docker build -t ${REPO}/frontend:${SHA}-baseline ./frontend &&
  docker push ${REPO}/backend:${SHA}-baseline &&
  docker push ${REPO}/frontend:${SHA}-baseline &&
  gcloud run services update aitrainer-backend --project ${GCP_PROJECT_ID} --region ${GCP_REGION} --image ${REPO}/backend:${SHA}-baseline &&
  gcloud run services update aitrainer-frontend --project ${GCP_PROJECT_ID} --region ${GCP_REGION} --image ${REPO}/frontend:${SHA}-baseline
'
```
Expected: saída com `real`, `user`, `sys` para baseline inicial.

- [ ] **Step 2: Registrar baseline com breakdown por etapa**

```markdown
## Baseline (2026-04-25)

| Etapa | Tempo Atual |
|---|---:|
| Build backend | 00:00 |
| Build frontend | 00:00 |
| Push backend | 00:00 |
| Push frontend | 00:00 |
| Deploy backend | 00:00 |
| Deploy frontend | 00:00 |
| Total | 00:00 |
```

- [ ] **Step 3: Commit**

```bash
git add docs/deploy/deploy-benchmark.md docs/deploy/production-deploy-runbook.md
git commit -m "docs: add deploy baseline timing"
```

### Task 2: Tornar Dockerfiles mais rápidos para produção

**Files:**
- Modify: `backend/Dockerfile`
- Modify: `backend-admin/Dockerfile`
- Modify: `frontend/Dockerfile`
- Modify: `frontend/admin/Dockerfile`

- [ ] **Step 1: Escrever teste de contrato para garantir que lint/typecheck não roda no build prod**

```bash
cd /home/colutti/projects/personal
rg -n "RUN npm run lint|RUN npm run typecheck|ruff check|pylint" frontend/Dockerfile backend/Dockerfile backend-admin/Dockerfile frontend/admin/Dockerfile
```
Expected: identificar os comandos que precisam sair da trilha de produção.

- [ ] **Step 2: Aplicar implementação mínima nos Dockerfiles**

```dockerfile
# frontend/Dockerfile (trecho alvo)
# Remover do build de produção:
# RUN npm run lint
# RUN npm run typecheck
# Manter apenas:
RUN npm run build
```

```dockerfile
# frontend/admin/Dockerfile (trecho alvo)
# Evitar npm ci duplicado no root e no admin quando não necessário.
# Estrutura esperada:
COPY admin/package*.json ./admin/
WORKDIR /app/admin
RUN npm ci
COPY admin/ ./
RUN npm run build
```

```dockerfile
# backend*.Dockerfile (trecho alvo)
# Build prod não deve instalar toolchain de verificação completa se não for necessário no runtime.
# Verificação permanece em jobs de CI, não no caminho do deploy.
```

- [ ] **Step 3: Validar build local rápido dos quatro serviços**

Run:
```bash
cd /home/colutti/projects/personal
docker build -t fityq-backend:test backend

docker build -t fityq-frontend:test frontend

docker build -t fityq-backend-admin:test backend-admin

docker build -t fityq-frontend-admin:test frontend
```
Expected: builds concluídos sem rodar lint/typecheck dentro do Docker build de produção.

- [ ] **Step 4: Rodar gates obrigatórios fora do Docker build**

Run:
```bash
cd /home/colutti/projects/personal/backend && .venv/bin/ruff check src tests && .venv/bin/pylint src
cd /home/colutti/projects/personal/backend-admin && .venv/bin/pylint src && .venv/bin/pyright src
cd /home/colutti/projects/personal/frontend && npm run lint && npm run typecheck
cd /home/colutti/projects/personal/frontend/admin && npm run lint && npm run typecheck
```
Expected: todos os gates verdes.

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend-admin/Dockerfile frontend/Dockerfile frontend/admin/Dockerfile
git commit -m "perf: decouple verification from production image builds"
```

### Task 3: Padronizar deploy sem perda de env vars

**Files:**
- Create: `scripts/deploy/preflight.sh`
- Create: `scripts/deploy/deploy_prod.sh`
- Create: `scripts/deploy/smoke_test.sh`
- Modify: `Makefile`

- [ ] **Step 1: Escrever teste/checagem falhando para garantir que deploy não usa `--set-env-vars`**

```bash
cd /home/colutti/projects/personal
rg -n "set-env-vars|env-vars-file" scripts/deploy/deploy_prod.sh
```
Expected: inicialmente ausente (arquivo novo), depois deve permanecer sem sobrescrever env completo.

- [ ] **Step 2: Implementar preflight com validações obrigatórias**

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?missing GCP_PROJECT_ID}"
: "${GCP_REGION:?missing GCP_REGION}"
: "${BACKEND_SERVICE:?missing BACKEND_SERVICE}"
: "${FRONTEND_SERVICE:?missing FRONTEND_SERVICE}"

gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .
gcloud run services describe "$BACKEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(metadata.name)'
gcloud run services describe "$FRONTEND_SERVICE" --project "$GCP_PROJECT_ID" --region "$GCP_REGION" --format='value(metadata.name)'
```

- [ ] **Step 3: Implementar deploy por atualização de imagem (preserva env existente)**

```bash
#!/usr/bin/env bash
set -euo pipefail

# deploy_prod.sh (trecho crítico)
gcloud run services update "$BACKEND_SERVICE" \
  --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" \
  --image "$BACKEND_IMAGE"

gcloud run services update "$FRONTEND_SERVICE" \
  --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" \
  --image "$FRONTEND_IMAGE"
```

- [ ] **Step 4: Adicionar smoke test pós deploy (inclui auth social)**

```bash
#!/usr/bin/env bash
set -euo pipefail

curl -fsS "$BACKEND_PUBLIC_URL/health" >/dev/null
curl -fsS "$FRONTEND_PUBLIC_URL/runtime-config.js" | grep -q "VITE_FIREBASE_API_KEY"
```

- [ ] **Step 5: Adicionar targets oficiais no Makefile**

```make
.PHONY: deploy-preflight deploy-prod deploy-smoke

deploy-preflight:
	./scripts/deploy/preflight.sh

deploy-prod: deploy-preflight
	./scripts/deploy/deploy_prod.sh

deploy-smoke:
	./scripts/deploy/smoke_test.sh
```

- [ ] **Step 6: Validar fluxo completo localmente em modo dry-run**

Run:
```bash
cd /home/colutti/projects/personal
bash scripts/deploy/preflight.sh
bash scripts/deploy/deploy_prod.sh --dry-run
bash scripts/deploy/smoke_test.sh --dry-run
```
Expected: comandos montados corretamente e sem flags destrutivas de env vars.

- [ ] **Step 7: Commit**

```bash
git add scripts/deploy/preflight.sh scripts/deploy/deploy_prod.sh scripts/deploy/smoke_test.sh Makefile
git commit -m "feat: add safe deploy pipeline that preserves Cloud Run env vars"
```

### Task 4: Pipeline CI/CD rápido com cache remoto

**Files:**
- Create: `.github/workflows/deploy-prod.yml`

- [ ] **Step 1: Escrever workflow manual com builds paralelos e cache no Artifact Registry**

```yaml
name: Deploy Prod

on:
  workflow_dispatch:
    inputs:
      ref:
        description: Git ref para deploy
        required: true
        default: main

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend]
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.ref }}
      - uses: docker/setup-buildx-action@v3
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker europe-southwest1-docker.pkg.dev --quiet
      - run: |
          docker buildx build \
            --platform linux/amd64 \
            --cache-from type=registry,ref=europe-southwest1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/aitrainer/${{ matrix.service }}:buildcache \
            --cache-to type=registry,ref=europe-southwest1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/aitrainer/${{ matrix.service }}:buildcache,mode=max \
            --tag europe-southwest1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/aitrainer/${{ matrix.service }}:${{ github.sha }} \
            --push \
            ${{ matrix.service == 'frontend' && './frontend' || './backend' }}
```

- [ ] **Step 2: Adicionar job de deploy que usa `gcloud run services update --image`**

```yaml
  deploy:
    needs: [build-and-push]
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - uses: google-github-actions/setup-gcloud@v2
      - run: |
          gcloud run services update aitrainer-backend \
            --region europe-southwest1 \
            --project ${{ secrets.GCP_PROJECT_ID }} \
            --image europe-southwest1-docker.pkg.dev/${{ secrets.GCP_PROJECT_ID }}/aitrainer/backend:${{ github.sha }}
```

- [ ] **Step 3: Validar sintaxe do workflow**

Run:
```bash
cd /home/colutti/projects/personal
python - <<'PY'
import yaml, pathlib
for p in pathlib.Path('.github/workflows').glob('*.yml'):
    yaml.safe_load(p.read_text())
print('workflow yaml ok')
PY
```
Expected: `workflow yaml ok`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy-prod.yml
git commit -m "ci: add cached production deploy workflow"
```

### Task 5: Documentação única e atualizada de deploy

**Files:**
- Modify: `GCP_DEPLOYMENT_GUIDE.md`
- Modify: `README.md`
- Create: `docs/deploy/production-deploy-runbook.md`
- Create: `scripts/deploy/README.md`

- [ ] **Step 1: Atualizar guia GCP com fluxo real e anti-regressão de env vars**

```markdown
## Regra crítica de produção
Nunca usar `--set-env-vars` ou `--env-vars-file` em deploy rotineiro.
Deploy padrão deve usar apenas `gcloud run services update --image ...` para preservar env vars existentes.
```

- [ ] **Step 2: Adicionar runbook de execução quando for solicitado deploy**

```markdown
# Production Deploy Runbook
1. `make deploy-preflight`
2. `make deploy-prod`
3. `make deploy-smoke`
4. validar login social e `/health`
```

- [ ] **Step 3: Adicionar seção no README com comando oficial único**

```markdown
## Production Deploy
Comando oficial:
```bash
make deploy-prod
```
```

- [ ] **Step 4: Revisar docs antigas e remover referências inválidas (`make gcp-*`, `scripts/deploy-cloudrun.sh`)**

Run:
```bash
cd /home/colutti/projects/personal
rg -n "make gcp-|deploy-cloudrun\.sh" README.md GCP_DEPLOYMENT_GUIDE.md ADMIN_DEPLOYMENT.md docs/deploy/production-deploy-runbook.md
```
Expected: nenhuma referência ao fluxo antigo no caminho oficial.

- [ ] **Step 5: Commit**

```bash
git add GCP_DEPLOYMENT_GUIDE.md README.md docs/deploy/production-deploy-runbook.md scripts/deploy/README.md
git commit -m "docs: consolidate fast and safe production deploy process"
```

### Task 6: Validação final de performance de deploy

**Files:**
- Modify: `docs/deploy/deploy-benchmark.md`

- [ ] **Step 1: Executar um deploy completo no novo fluxo e medir tempo**

Run:
```bash
cd /home/colutti/projects/personal
/usr/bin/time -p make deploy-prod
```
Expected: tempo total significativamente menor que baseline (meta < 8 min no caminho quente com cache).

- [ ] **Step 2: Executar smoke pós deploy**

Run:
```bash
cd /home/colutti/projects/personal
make deploy-smoke
```
Expected: health e runtime config ok, sem regressão em login social.

- [ ] **Step 3: Atualizar benchmark comparativo antes/depois**

```markdown
## Resultado
- Baseline: 15m+
- Novo fluxo (cold): 9-12m
- Novo fluxo (warm cache): 4-8m
- Regressão de env vars em produção: 0 ocorrências
```

- [ ] **Step 4: Commit**

```bash
git add docs/deploy/deploy-benchmark.md
git commit -m "docs: record deploy performance gains and env safety results"
```

## Self-Review

### 1) Spec coverage
- Reduzir tempo de deploy: coberto nas Tasks 2, 4 e 6.
- Atualizar documentação `.md`: coberto na Task 5.
- Container-first: coberto nas Tasks 2 e 4 (Dockerfiles + buildx cache).
- “Quando eu pedir deploy você não tem que saber exatamente o que fazer”: coberto na Task 3 (scripts + Make targets) e Task 5 (runbook único).
- Evitar perda de env vars de produção (histórico de falha com login social): coberto na Task 3 (deploy com `services update --image` sem sobrescrever env) e Task 5 (regra explícita na doc).

### 2) Placeholder scan
- Não há `TODO/TBD` operacionais no fluxo alvo.
- Todos os passos têm comando, snippet ou critério esperado.

### 3) Type consistency
- Nomes de alvos e scripts estão consistentes: `deploy-preflight`, `deploy-prod`, `deploy-smoke` e `scripts/deploy/*.sh`.
