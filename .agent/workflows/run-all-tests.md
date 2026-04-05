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

## 0. Regras de Execução

- O caminho oficial é 100% containerizado.
- Não executar `pytest`, `npm test` ou `npx playwright test` no host como validação oficial.
- Cada execução de `make verify`, `make verify-all`, `make test-once` e `make e2e` usa projeto Compose descartável e isolado.
- Após qualquer feature, bugfix ou refactor relevante, executar `make test-once` completo antes de concluir.

---

## 1. Qualidade Rápida

```bash
make security-check                         # Semgrep + Trivy + Secret Scanning
```

---

## 2. Suíte Completa

```bash
make test-once
```

Esse comando já executa:
- backend verify (lint + testes)
- backend-admin verify (lint + typecheck)
- frontend verify (lint + typecheck + testes)
- frontend-admin verify (lint + typecheck + testes)
- e2e Playwright no stack containerizado

---

## 3. Comandos Específicos

```bash
make verify        # gate rápido sem e2e
make verify-all    # gate completo + segurança
make e2e           # apenas e2e containerizado
```

---

## Regras de Ouro
- **Bug = Teste Primeiro**: Crie um teste que falhe para reproduzir o bug antes da correção.
- **Sem Exceções no Host**: validação oficial é sempre por `make` + containers.
- **Zero Warnings**: trate warnings como falhas.
- **Ambiente descartável**: stack de teste deve ser isolado, efêmero e removido ao fim.
