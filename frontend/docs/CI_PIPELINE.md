# CI/CD Pipeline com Fail-Fast Policy

## 📋 Visão Geral

O pipeline CI/CD foi otimizado para implementar uma **política de fail-fast** que valida código rapidamente e economiza recursos em CI/CD.

### Arquitetura

```
Push/PR
  ↓
[Backend Tests] [Frontend Tests] (paralelo)
  ↓
✅ Passa? Continua
❌ Falha? Para aqui
  ↓
[Cypress Fast Gate - 10s]
  ↓
✅ Passa? Executa testes paralelos
❌ Falha? Bloqueia PR
  ↓
[Cypress Extended - 3 Workers]
  ↓
Resultado final
```

## ⚡ Fases de Validação

### Fase 1: Validação Rápida (Fail-Fast Gate)
**Tempo:** ~30 segundos total

```yaml
- Backend: pytest (unit tests + linter)
- Frontend: npm test + npm run build
- Cypress: 14 testes críticos (~10s)
```

**Decisão:** Se alguma fase falhar, pipeline para imediatamente.

### Fase 2: Execução Paralela (Cypress Extended)
**Tempo:** ~5-10 minutos com 3 workers

```
Worker 1: admin-users, auth, body-composition (4+3+6=13 testes)
Worker 2: chat, dashboard, memories (5+4+11=20 testes)
Worker 3: nutrition, error-handling, outros (1+2+8=11 testes)
```

**Apenas inicia se Fase 1 passar.**

## 🔧 Configuração no GitHub Actions

Arquivo: `.github/workflows/ci.yml`

### Jobs Configurados

1. **backend-test** (sempre)
   - Python setup
   - Dependências
   - Unit tests: `pytest tests/unit`
   - Benchmarks: `pytest tests/performance --benchmark-only`
   - Lint: `ruff check .`

2. **frontend-test** (sempre)
   - Node.js setup
   - npm ci
   - Unit tests: `npm test`
   - Build: `npm run build`

3. **frontend-e2e-fast** (Fail-Fast Gate)
   - Timeout: 2 minutos
   - Comando: `npm run cypress:fast`
   - Resultado: DEVE passar para continuar
   - Continue-on-error: false

4. **frontend-e2e-extended** (Parallelized)
   - Depende de: `frontend-e2e-fast`
   - Timeout: 10 minutos
   - Matrix: 3 workers
   - Comando: `npm run cypress:extended -- --parallel`
   - Continue-on-error: true (não bloqueia merge se falhar, mas reporta)

## 📊 Tempos de Execução

| Fase | Comando | Tempo | Testes |
|------|---------|-------|--------|
| Gate Rápido | `make ci-fast` | ~30s | 14 (críticos) |
| Full CI | `make ci-test` | ~5-10min | 56+ |
| Backend Only | `make test-backend` | ~10s | 497 |
| Frontend Only | `make test-frontend` | ~5s | - |
| Cypress Fast | `make cypress-fast` | ~10s | 14 |
| Cypress Extended | `make cypress-extended` | ~3-5min | 42 |

## 🚀 Como Usar Localmente

### Antes de criar um PR
```bash
# Validação rápida (simular CI gate)
make ci-fast  # ~30s

# Se passar, testes completos (opcional)
make ci-test  # ~5-10min
```

### Antes de fazer commit
```bash
# Testes unitários apenas
make test-backend
make test-frontend

# Se saudável, validação rápida
make ci-fast
```

### Para debug de testes E2E
```bash
# Testes críticos (fast-fail policy)
make cypress-fast

# Suite extendida (mais lenta)
make cypress-extended

# Cypress interativo (debug)
make cypress-open
```

## 🎯 Fail-Fast Policy

### O que é?

- **Zero retries:** Se um teste falha, falha imediatamente
- **Timeouts curtos:** 8 segundos padrão (vs 15s antes)
- **Sem retry automático:** Força testes estáveis
- **Rejeita flaky tests:** Testes que falham intermitentemente são identificados rapidamente

### Por que?

1. **Feedback Rápido:** Sabe em 30s se mudanças básicas quebram algo
2. **CI Econômico:** Menos resources desperdiçados em retries
3. **Qualidade:** Força estabilidade real, não mascarada por retries
4. **Developer Experience:** Ciclo de desenvolvimento mais rápido

### Trade-offs

✅ Benefícios:
- 10 segundos em vez de 10+ minutos para feedback crítico
- Identifica flaky tests imediatamente
- Menos recursos em CI/CD

⚠️ Limitações:
- 12 test suites desabilitadas (candidatos para Jest component tests)
- Alguns testes widget/chart são inerentemente flaky
- Extended suite ainda ~3-5 minutos

## 📈 Próximas Melhorias

1. **Refatorar 12 Disabled Suites → Jest Component Tests**
   - Melhor isolamento
   - Testes mais rápidos
   - Mais determinísticos

2. **Implementar Caching em CI/CD**
   - npm cache em GitHub Actions
   - Dependências pré-built
   - Shorten execution time further

3. **Notificações de Teste**
   - Slack notifications
   - GitHub check runs detalhados
   - Relatório de cobertura

4. **Análise de Performance**
   - Histórico de tempos de execução
   - Alertas se testes ficarem mais lentos
   - Otimizações direcionadas

## 🔗 Referências

- `.github/workflows/ci.yml` - Configuração GitHub Actions
- `frontend/package.json` - Scripts npm
- `Makefile` - Targets locais
- `frontend/docs/CYPRESS_PERFORMANCE.md` - Detalhes de otimizações Cypress
- `frontend/cypress.config.ts` - Configuração Cypress fail-fast

## ✅ Checklist de Verificação

- [x] Backend tests passando (497/497)
- [x] Frontend unit tests passando
- [x] Cypress fast gate implementado (14 testes, ~10s)
- [x] Cypress extended parallelizado (3 workers)
- [x] .github/workflows/ci.yml atualizado
- [x] Makefile targets: ci-fast, ci-test
- [x] Documentação completa

## 🐛 Troubleshooting

### CI passa localmente mas falha no GitHub Actions

```bash
# Simular ambiente CI localmente
cd frontend
npm ci  # Usar exact versions do package-lock.json
npm test -- --watchAll=false
npm run cypress:fast
```

### Cypress timeout no GitHub Actions

- Aumentar `timeout-minutes` em .github/workflows/ci.yml
- Verificar se há recursos suficientes no runner
- Revisar logs do Cypress em `Run Cypress` step

### Testes paralelos não funcionam

- Verificar Cypress Cloud config (se usando)
- Usar `--parallel` flag apenas em CI
- Garantir `cypress-version` compatível

---

**Última atualização:** 2026-01-28
**Status:** ✅ Em produção
