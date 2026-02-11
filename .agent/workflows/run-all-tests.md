---
description: Executa a suíte completa de testes e verificação de qualidade do projeto (Backend & Frontend)
---

### 1. Preparação do Ambiente Backend
// turbo
1. Verifique se as dependências do sistema estão instaladas no container backend.
   - Execute: `podman exec personal_backend_1 bash -c "dpkg -l | grep libatomic1 || (apt-get update && apt-get install -y libatomic1)"`

### 2. Verificação de Qualidade Backend (Zero Tolerância)
// turbo
1. Linting (Ruff): `podman exec personal_backend_1 /opt/venv/bin/ruff check .`
// turbo
2. Linting (Pylint): `podman exec personal_backend_1 /opt/venv/bin/pylint src`
// turbo
3. Type Checking (Pyright): `podman exec personal_backend_1 /opt/venv/bin/pyright`
   - **Nota**: Se houver erros de "import-outside-toplevel" ou "too-many-locals", avalie se deve refatorar ou adicionar `# pylint: disable=...` com parcimônia.

### 3. Testes Backend
// turbo
1. Execute os testes unitários e de integração: `podman exec personal_backend_1 pytest`
   - Se houver falhas, corrija-as imediatamente. Não avance sem que o backend esteja 100% verde.

### 4. Verificação de Qualidade Frontend
// turbo
1. Linting: `cd frontend && npm run lint`
// turbo
2. Type Checking: `cd frontend && npm run typecheck`

### 5. Testes Frontend
// turbo
1. Testes Unitários e Cobertura: `cd frontend && npx vitest run --coverage`
   - **Atenção**: Se a cobertura falhar por pouco, ajuste os thresholds em `vitest.config.ts` para refletir o estado atual, mas não diminua drasticamente.
// turbo
2. Testes E2E (Opcional, mas recomendado se houver mudanças visuais/fluxo): `cd frontend && npx playwright test`

### 6. Limpeza e Relatório
// turbo
1. Remova artefatos gerados:
   - Backend: `.pytest_cache`, `__pycache__`, `.ruff_cache`
   - Frontend: `coverage/`, `playwright-report/`, `test-results/`
   - Comando: `rm -rf frontend/coverage frontend/playwright-report frontend/test-results frontend/coverage_report.txt`
   - Remova outros arquivos temporarios, como arquivos do pyright, arquivos txt nao sejam usados
   - Remova arquivos gerados por voce para testes temporarios.

2. Produza um relatório final contendo:
   - Status dos linters (deve ser "Clean").
   - Total de testes passados no backend e frontend.
   - Cobertura atual do frontend.
   - Lista de problemas corrigidos durante a execução.

**Regras de Ouro:**
- **Zero Warnings/Errors**: Não ignore warnings dos linters.
- **Frontend Isolado**: Testes de frontend não devem depender do backend rodando (use mocks/msw).
- **Backend Robusto**: Testes de backend devem garantir a integridade da API e lógica de negócios.
- Se detectar algo que deveria estar nessas instrucoes, ao final do testes atualize-as nesse arquivo. Seja breve e mantenha esse arquivo atualizado.