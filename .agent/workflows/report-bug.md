---
description: Fluxo de correção de bugs com TDD obrigatório
---

### 1. Investigação e Reprodução
1. Analise o bug reportado e identifique o código suspeito.
2. **CRÍTICO**: Escreva um teste automatizado que falhe reproduzindo exatamente o comportamento indesejado.

### 2. Correção (Ciclo TDD)
1. Implemente a correção mínima necessária para fazer o teste passar.
2. Certifique-se de que o teste agora está verde.
3. Refatore o código se necessário, mantendo o teste verde.

### 3. Verificação de Regressão
1. Execute outros testes relacionados para garantir que nada foi quebrado.
2. **Execute o workflow `run-all-tests.md`** para garantir que a qualidade geral (lint/types) se mantém.
3. Crie testes automatizados para que o problema nao volte a acontecer sempre que possivel.

### 4. Relatório
1. Informe a causa raiz determinada.
2. Explique como o teste prova que o bug foi resolvido e não voltará.
3. Informe se há ações extras necessárias em produção (ex: migrações de banco).

**Regra Principal**: Se não há um teste que falha antes da correção, você ainda não entendeu o bug.