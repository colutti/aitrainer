---
description: Executa a suíte suportada de testes e verificação de qualidade do projeto
---

# Workflow: Execução de Testes e Qualidade

Este guia define os comandos atuais de validação do repositório.

## Caminho oficial

Para a suíte completa com ambiente consistente, use:

```bash
make test-once
```

Esse é o caminho suportado para validação completa do sistema.

## 1. Backend principal

Qualidade:

```bash
cd backend
.venv/bin/ruff check src tests
.venv/bin/pylint src
```

Testes:

```bash
cd backend
.venv/bin/pytest
.venv/bin/pytest tests/conversation/ -v
.venv/bin/pytest --cov=src
```

## 2. Backend admin

```bash
cd backend-admin
.venv/bin/pylint src
.venv/bin/pyright src
```

## 3. Frontend principal

```bash
cd frontend
npm run lint
npm run typecheck
npm test
```

## 4. Frontend admin

```bash
cd frontend/admin
npm run lint
npm run typecheck
npm test
```

## 5. E2E

O caminho suportado para E2E é containerizado:

```bash
make e2e
make verify-all
make test-once
```

Não trate `npx playwright test` local como validação oficial do projeto.

## 6. Regras de fechamento

- Trate warnings como falhas.
- Use os executáveis do `.venv` quando existir ambiente virtual local.
- Se a tarefa tocar múltiplas superfícies, rode a validação de cada uma delas.
- Se a limpeza fizer parte do fechamento, siga `.agent/workflows/cleancode.md`.
