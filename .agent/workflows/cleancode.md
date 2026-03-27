---
description: Limpeza profunda de arquivos temporários e caches
---

# Workflow: Clean Codebase Artifacts

Use este workflow para remover apenas artefatos locais gerados por testes, build e execução.

## Escopo seguro

- Limpar `tmp/` na raiz do projeto
- Limpar caches Python (`*.pyc`, `__pycache__`, `.pytest_cache`, `.ruff_cache`)
- Limpar artefatos de cobertura e relatórios (`frontend/coverage`, `frontend/playwright-report`)
- Remover logs e arquivos temporários gerados localmente, desde que não façam parte do código-fonte

## Não fazer sem pedido explícito

- Não apagar branches git
- Não remover worktrees
- Não apagar arquivos de configuração, documentação ou scripts do projeto
- Não usar comandos destrutivos fora do workspace atual

## Comandos sugeridos

```bash
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -prune -exec rm -rf {} +
rm -rf tmp/*
rm -rf backend/.pytest_cache backend/.ruff_cache
rm -rf frontend/coverage frontend/playwright-report
rm -rf frontend/admin/coverage
```

## Verificação

- Rode os comandos de `.agent/workflows/run-all-tests.md` se a limpeza fizer parte do fechamento de uma tarefa.
