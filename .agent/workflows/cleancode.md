---
description: Limpeza profunda de arquivos temporários e caches
---

- Limpe o projeto atual inteiro eliminando arquivos de logs, scripts temporários, pastas de testes como `.coverage`.
- Siga a seção de limpeza do `run-all-tests.md`:
  - Delete arquivos em `tmp/` na raiz.
  - Delete caches de Python: `find . -name "*.pyc" -delete && find . -name "__pycache__" -delete`.
  - Delete artefatos de testes: `.pytest_cache`, `.ruff_cache`, `frontend/coverage`, etc.
- Remova branches locais e worktrees que não são mais usados para manter o ambiente leve.