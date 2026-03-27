---
description: Executa a suíte completa de testes e verificação de qualidade do projeto (Backend, Frontend & E2E)
---

# Workflow: Execução de Testes e Qualidade

Este guia define os comandos e padrões para garantir que o projeto mantenha **Zero Erros** e **Zero Warnings** em todas as camadas.

## Caminho oficial

Para a suíte completa com ambiente consistente, use:

```bash
make test-once
```

Esse comando sobe MongoDB, Qdrant, backend real, frontend real e Playwright em containers na mesma rede.

## 0. Caminhos e Ferramentas (Referência Rápida)

Sempre utilize os executáveis dos ambientes virtuais locais para garantir paridade:

- **Backend**: `backend/.venv/bin/` (pytest, ruff, pyright, pylint)
- **Frontend**: `frontend/` (npm, npx playwright)
- **Frontend Admin**: `frontend/admin/` (npm)

---

## 1. Backend: Qualidade e Testes

### Verificação de Qualidade (Lint & Types)
```bash
cd backend
.venv/bin/ruff check src                    # Lint rápido
.venv/bin/pylint src                        # Lint profundo (Meta: 10/10)
.venv/bin/pyright src                       # Verificação de Tipos estrita
```

### Suíte de Testes (TDD)
```bash
cd backend
.venv/bin/pytest                            # Todos os testes
.venv/bin/pytest tests/integration/ -v      # Apenas integração (novos testes)
.venv/bin/pytest --cov=src                  # Relatório de cobertura
```

---

## 2. Backend Admin: Qualidade

```bash
cd backend-admin
.venv/bin/python -m pytest || true          # Opcional: atualmente o foco principal é lint/typecheck
.venv/bin/pylint src                        # Meta: 10/10
.venv/bin/pyright src
```

---

## 3. Frontend: Qualidade e Testes (Main & Admin)

### Frontend Principal (App)
```bash
cd frontend
npm run check                               # Atalho: lint + typecheck + testes
npm run lint                                # ESLint (Strict)
npm run typecheck                           # TypeScript (noEmit)
npm test                                    # Unitários (Vitest)
npm run test:coverage -- src/features/onboarding  # Cobertura por feature
```

### Frontend Admin
```bash
cd frontend/admin
npm run check
```

---

## 4. Testes End-to-End (E2E) Automáticos

Os testes E2E rodam em modo **Headless** contra um **Build de Produção** local para garantir estabilidade máxima e evitar erros de servidor de desenvolvimento.

```bash
cd frontend
# Execução automática padrão
npx playwright test --project=chromium --reporter=list
```

---

## 5. Segurança (SAST + SCA)

```bash
make security-check                         # Semgrep + Trivy + Secret Scanning
```

---

## 6. Limpeza e Relatório Final

Sempre limpe artefatos antes de considerar a tarefa concluída:

1. **Limpeza**: remova apenas artefatos gerados localmente, conforme `.agent/workflows/cleancode.md`
2. **Relatório**: O Agente deve reportar:
   - Status do Lint (Zero Erros).
   - Status dos Tipos (Zero Erros).
   - Total de testes passados.
   - Cobertura aproximada das áreas afetadas.

---

## Regras de Ouro
- **Bug = Teste Primeiro**: Crie um teste que falhe para reproduzir o bug antes da correção.
- **Headless por Padrão**: Nunca inicie processos interativos ou watchers no ambiente de automação.
- **Zero Warnings**: Trate warnings como erros. Não os silencie com `# noqa` ou `ignore`, corrija a raiz.
- **Ambiente Isolado**: Prefira os binários do `.venv` aos globais do sistema.
