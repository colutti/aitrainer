# Deploy Benchmark

## Contexto
Medições coletadas em **25/04/2026** no fluxo de produção Cloud Run com builds no Cloud Build (`europe-southwest1`).

## Resultados

| Cenário | Build backend (inclui upload) | Build frontend (inclui upload) | Build total | Deploy+Smoke | Tempo total one-shot |
|---|---:|---:|---:|---:|---:|
| Baseline inicial do novo fluxo (`make deploy-prod`) | ~7m27s (paralelo) | ~7m27s (paralelo) | 7m27s | 57s | **8m33s** |
| One-shot após otimizações fase 2 (`make deploy-prod`) | ~5m26s (paralelo) | ~5m26s (paralelo) | 5m26s | 53s | **6m27s** |
| Build quente com cache remoto (antes de `.gcloudignore`) | ~5m32s (paralelo) | ~5m32s (paralelo) | 5m32s | n/a | **5m41s** (build-only) |
| Build quente com cache remoto + `.gcloudignore` | ~5m27s (paralelo) | ~5m27s (paralelo) | 5m27s | n/a | **5m36s** (build-only) |
| Build quente + split runtime/dev deps Python | ~4m39s (paralelo) | ~4m39s (paralelo) | 4m40s | n/a | **4m48s** (build-only) |
| `deploy-prod-fast` sem mudanças (`BASE_REF=HEAD`) | n/a | n/a | 0s | ~4s + smoke | **~4s** (no-op seguro) |

## Ganhos observados

- Deploy one-shot real em produção melhorou de **8m33s** para **6m27s**.
- Build quente recorrente estabilizou em ~**5m36s**.
- Build quente após otimizações de deps Python ficou em **4m48s**.
- Upload de contexto do backend caiu de ~**764.6 MiB** para ~**893.8 KiB** após `.gcloudignore`.
- Upload de contexto do frontend caiu de ~**21.9 MiB** para ~**18.4 MiB**.
- Modo incremental `deploy-prod-fast` evita rebuild/redeploy quando não há mudanças relevantes.

## Próximos incrementos (se alvo <5min total)

1. Avaliar troca de Kaniko para BuildKit remoto (`docker buildx bake`) com cache registry inline.
2. Criar imagem base versionada para backend com dependências congeladas por lockfile.
3. Adotar lock de dependências Python (ex.: `pip-compile`) para resolver mais rápido e com cache estável.
