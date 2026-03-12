---
description: Executa a suíte completa de testes e verificação de qualidade do projeto (Backend & Frontend)
---

### 0. Guia de Ferramentas e Caminhos (Para o Agente)
// turbo
1. **Ambiente Local (Venv)**: Sempre dê preferência aos executáveis dentro da pasta `.venv` do backend para evitar confusão de versões:
   - Python: `backend/.venv/bin/python`
   - Pyright: `backend/.venv/bin/pyright`
   - Ruff: `backend/.venv/bin/ruff`
   - Pytest: `backend/.venv/bin/pytest`
   - Pylint: `backend/.venv/bin/pylint` ou `backend/.venv/bin/python -m pylint`

2. **Container (Podman)**: Caso prefira rodar no container para garantir paridade com prod:
   - Ruff: `podman exec personal_backend_1 /opt/venv/bin/ruff check .`
   - Pylint: `podman exec personal_backend_1 /opt/venv/bin/pylint src`
   - Testes: `podman exec personal_backend_1 pytest`

### 1. Preparação do Ambiente Backend
// turbo
1. Verifique se as dependências do sistema estão instaladas no container backend (se estiver usando containers).
   - Execute: `podman exec personal_backend_1 bash -c "dpkg -l | grep libatomic1 || (apt-get update && apt-get install -y libatomic1)"`

### 2. Verificação de Qualidade Backend (Zero Tolerância)
// turbo
1. **Linting (Ruff)**: `cd backend && .venv/bin/ruff check src`
// turbo
2. **Linting (Pylint)**: `cd backend && .venv/bin/pylint src` (Deve ser 10.00/10)
// turbo
3. **Type Checking (Pyright)**: `cd backend && .venv/bin/pyright src`
   - **Nota**: Se houver erros de "import-outside-toplevel" em handlers de ferramentas de IA ou outros padrões específicos do projeto, use `# pylint: disable=...` apenas se for estritamente necessário e documentado.

### 3. Testes Backend (TDD Obrigatório)
// turbo
1. Execute os testes unitários e de integração: `cd backend && .venv/bin/pytest`
   - **Regra TDD**: Para novas features ou correção de bugs, o teste falhando deve existir ANTES da correção.
   - **Cobertura**: Use `cd backend && .venv/bin/pytest --cov=src` se precisar verificar gaps de testes.

### 4. Admin Backend (Acesso Isolado)
// turbo
1. Linting & Type Check (Admin): `cd backend-admin && .venv/bin/pylint src`
   - **Nota**: Manter nota 10/10 no pylint.

### 5. Verificação de Qualidade Frontend (Main & Admin)
// turbo
1. **Linting (Main)**: `cd frontend && npm run lint`
// turbo
2. **Type Checking (Main)**: `cd frontend && npm run typecheck`
// turbo
3. **Linting & Type Check (Admin)**: `cd frontend/admin && npm run lint && npm run typecheck`

### 6. Testes Frontend
// turbo
1. **Testes Unitários (Main)**: `cd frontend && npm test`
// turbo
2. **Testes Unitários (Admin)**: `cd frontend/admin && npm test`
// turbo
3. **Testes E2E (Playwright)**: `cd frontend && npx playwright test` (Opcional, mas recomendado para fluxos críticos).

### 7. Security Scanning (SAST + SCA + Secrets)
// turbo
1. **Security Check**: `make security-check` (ou rode individualmente Semgrep e Trivy via podman).

### 8. Limpeza e Relatório
// turbo
1. **Limpeza Profunda**:
   - Delete arquivos temporários: `rm -rf tmp/*`
   - Delete caches: `find . -name "*.pyc" -delete && find . -name "__pycache__" -delete`
   - Delete artefatos de testes: `rm -rf backend/.pytest_cache frontend/coverage frontend/playwright-report`
   - Delete logs desnecessários e arquivos de POC gerados por você.

2. **Produza um relatório final**:
   - Status dos linters (Zero Errors/Warnings).
   - Total de testes passados.
   - Resumo das correções feitas.

**Regras de Ouro:**
- **Bug = Teste primeiro**: Nunca corrija um bug sem antes provar que ele existe com um teste automatizado.
- **Zero Warnings**: Warnings são erros disfarçados. Corrija a raiz, não silencie (a menos que seja genuinamente necessário).
- **Caminhos Curtos**: Use os caminhos definidos no passo 0 para ser rápido e preciso.
- **Limpeza**: Nunca deixe lixo (logs, screenshots, scripts .py temporários) no repositório.