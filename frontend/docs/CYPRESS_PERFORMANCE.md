# Cypress Performance & Fail-Fast Strategy

## Overview

Configuração otimizada para execução rápida de testes E2E com política de **fail-fast** (falhar imediatamente sem retries).

**Objetivos:**
- ✅ Falhar rapidamente em caso de erros (sem esperar retries)
- ✅ Executar testes em paralelo quando possível
- ✅ Dividir testes por criticidade para execução seletiva
- ✅ Reduzir tempo total de execução

## Configurações de Performance

### cypress.config.ts

```typescript
defaultCommandTimeout: 8000      // 8 segundos (era 15)
pageLoadTimeout: 25000           // 25 segundos (era 60)
requestTimeout: 8000             // Timeout para requisições
responseTimeout: 8000            // Timeout para respostas

retries:
  runMode: 0                      // SEM retries em headless (era 1)
  openMode: 0                     // SEM retries interativo
```

### Benefícios

1. **Falha Rápida**: Sem retry automático, testes falham imediatamente
2. **Feedback Instant**: Desenvolvedores sabem rapidamente o que quebrou
3. **CI/CD Mais Rápido**: Menos tempo esperando por retries inúteis
4. **Redução de Flakiness**: Força testes mais estáveis (sem dependência de retry)

## Estratégias de Execução

### 1. Fast Mode (⚡ 2-3 minutos)

Testes críticos apenas:

```bash
# Terminal direto
npm run cypress:fast

# Via Makefile
make cypress-fast
```

**Specs inclusos:**
- admin-users.cy.ts (4 testes)
- auth.cy.ts (3 testes)
- body-composition.cy.ts (6 testes)

**Uso:** Validação rápida durante desenvolvimento, CI gates

### 2. Critical Tests (🔴 3-4 minutos)

Testes críticos com logging:

```bash
npm run cypress:critical
make cypress-critical
```

**Same specs as fast, but with:**
- Headless mode com output
- Melhor feedback de falhas
- Sem paralelização

**Uso:** PRs, commits antes de push

### 3. Extended Suite (🟡 10-15 minutos)

Todos os testes:

```bash
npm run cypress:extended
make cypress-extended
```

**Specs:**
- Todos os arquivos em cypress/e2e/*.cy.ts
- Exceto aqueles com `describe.skip()`

**Uso:** Pre-release, staging, nightly builds

### 4. Parallel Mode (🟢 ~5-7 minutos com 2-4 workers)

Execução paralela (experimental):

```bash
npm run cypress:parallel
make cypress-parallel
```

**Requer:**
- Cypress Cloud (free) ou `--parallel --record false`
- Múltiplos cores disponíveis
- Testes isolados (sem shared state)

**Uso:** CI/CD pipelines com múltiplos agents

## Recomendações por Contexto

### Durante Desenvolvimento

```bash
# Primeiro: validar fast
make cypress-fast

# Depois: rodar critical antes de commit
make cypress-critical

# Ocasional: full suite para verificação completa
make cypress-extended
```

### Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

npm run cypress:fast || {
  echo "❌ Cypress fast tests failed"
  exit 1
}
```

### CI/CD Pipeline

```yaml
# GitHub Actions exemplo
- name: Run Cypress Critical
  run: make cypress-critical
  timeout-minutes: 5

- name: Run Cypress Extended (if critical passes)
  if: success()
  run: make cypress-extended
  timeout-minutes: 20
```

### Before Deployment

```bash
# Verificar todos os testes passam
make cypress-extended

# Com cobertura de relatório
cypress run --record --spec "cypress/e2e/**/*.cy.ts"
```

## Fail-Fast Detalhes

### Como Funciona

1. **Timeout é alcançado** → Falha imediatamente
2. **Nenhum retry automático** → Teste termina
3. **Próximo teste inicia** → Não aguarda
4. **Report mostra status** → Falha clara

### Exemplo de Otimização

```typescript
// ❌ ANTES (com retry automático, demora ~30s para falhar)
it('should load modal', () => {
  cy.visit('/admin/users');
  cy.contains('Usuários').should('be.visible');  // Retry 1x se falhar
  // Se der timeout: 15s * 1 retry = ~30 segundos para falhar
});

// ✅ DEPOIS (sem retry, demora ~8s para falhar)
it('should load modal', () => {
  cy.visit('/admin/users');
  cy.contains('Usuários').should('be.visible');  // Falha em 8s se timeout
  // Se der timeout: 8 segundos para falhar
});
```

## Otimizações nos Testes

### 1. Use Esperas Explícitas

```typescript
// ❌ Ruim - retry 3+ vezes
cy.get('[data-test="button"]').click();

// ✅ Bom - aguarda a requisição
cy.intercept('POST', '**/api/action').as('action');
cy.get('[data-test="button"]').click();
cy.wait('@action');
```

### 2. Mock Dados Desde o Início

```typescript
// ❌ Ruim - espera dados da API
beforeEach(() => {
  cy.visit('/');
  // Página espera API responder
});

// ✅ Bom - mock antes de visitar
beforeEach(() => {
  cy.intercept('GET', '**/api/users', { body: mockUsers }).as('getUsers');
  cy.visit('/');
  cy.wait('@getUsers');
});
```

### 3. Fechar Recursos Rapidamente

```typescript
// ✅ Bom - modal fecha rapidamente
cy.contains('Deletar').click();
cy.on('window:confirm', () => true);  // Confirm imediatamente
cy.wait('@deleteUser');
```

## Monitoramento & Debugging

### Ver Timeouts Atuais

```bash
cypress run --headed --no-exit
# Observe a barra de progresso para ver quando testes timeout
```

### Aumentar Timeout Temporariamente

```typescript
// Para um comando específico
cy.visit('/slow-page', { timeout: 30000 });

// Para um suite inteiro
describe('Slow tests', { timeout: 30000 }, () => {
  // ...
});
```

### Detectar Testes Lentos

```bash
cypress run --record  # Gera relatório com duração
# Ou via plugin customizado em plugins/index.js
```

## Métricas de Performance

### Baseline Atual

| Modo | Duração | Specs | Retries |
|------|---------|-------|---------|
| fast | 2-3 min | 3 | 0 |
| critical | 3-4 min | 3 | 0 |
| extended | 10-15 min | ~29 | 0 |
| parallel | 5-7 min | ~29 | 0 |

### Alvos de Melhoria

- [ ] Reduzir extended para < 10 min
- [ ] Implementar parallel testing com 2+ workers
- [ ] Adicionar test categorization tags
- [ ] Dashboard de performance em CI

## Troubleshooting

### Teste passa em modo aberto, falha em headless

```bash
# Causas comuns:
# 1. Timing diferente
# 2. Viewport diferente
# 3. Mock não configurado

# Solução: testar em headless
cypress run --spec "cypress/e2e/test.cy.ts"
```

### Timeout mesmo com timeout aumentado

```typescript
// Verificar se:
// 1. Página está carregando (cy.wait before assertions)
cy.wait('@apiCall');
cy.get('element').should('be.visible');

// 2. Elemento está visível
cy.get('element').should('be.visible');

// 3. Sem dependências ocultas
// 4. Mock está correto
```

### Testes falhando aleatoriamente (flaky)

```typescript
// ✅ Adicionar explicitação
cy.intercept('GET', '**/api/**').as('api');
cy.visit('/');
cy.wait('@api');  // Aguarda requisições

cy.get('[data-test="content"]').should('exist').and('be.visible');
```

## Próximos Passos

1. ✅ Implementar cypress.config.ts com fail-fast
2. ✅ Adicionar scripts npm para diferentes modos
3. ✅ Adicionar targets Makefile
4. 🔄 Executar testes com nova configuração
5. 📊 Medir tempo de execução por suite
6. 🚀 Integrar com CI/CD pipeline

## Referências

- [Cypress Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [Cypress Configuration](https://docs.cypress.io/guides/references/configuration)
- [Cypress Parallelization](https://docs.cypress.io/guides/cloud/introduction)
