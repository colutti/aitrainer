# Guia de Execução de Testes Frontend

## Quick Start

### Rodar Todos os Testes (Jest + Cypress)
```bash
cd frontend

# Jest unit tests com coverage
npm test -- --coverage

# Cypress E2E tests (headless)
npm run cypress:run

# Cypress E2E tests (interactive)
npm run cypress:open
```

---

## Jest Unit Tests

### Executar Tudo
```bash
npm test
```

### Executar com Coverage
```bash
npm test -- --coverage
```

**Output esperado:**
- Coverage report em `coverage/lcov-report/index.html`
- Métricas: Statements, Branches, Functions, Lines
- Target: 80%+ coverage

### Executar Arquivo Específico
```bash
npm test -- chat.service.spec.ts
npm test -- chat.component.spec.ts
npm test -- date-format.pipe.spec.ts
```

### Watch Mode (desenvolvimento)
```bash
npm test -- --watch
```

Útil para TDD - testes rodam automaticamente conforme você edita.

### Executar Apenas Testes Específicos
```bash
# Por padrão no nome
npm test -- --testNamePattern="should create"

# Por arquivo
npm test -- --testPathPattern="services"
npm test -- --testPathPattern="components/chat"
npm test -- --testPathPattern="pipes"
```

### Detectar Testes Lentos
```bash
npm test -- --detectOpenHandles
npm test -- --logHeapUsage
```

---

## Cypress E2E Tests

### Modo Headless (CI/CD)
```bash
npm run cypress:run
```

Testa todos os cenários automaticamente.

### Modo Interactive (desenvolvimento)
```bash
npm run cypress:open
```

Interface visual para:
- Selecionar testes individuais
- Ver cada passo da execução
- Debug com DevTools
- Reexecutar falhas rapidamente

### Executar Suite Específico
```bash
npx cypress run --spec "cypress/e2e/onboarding.cy.ts"
npx cypress run --spec "cypress/e2e/error-scenarios.cy.ts"
```

### Executar com Browser Específico
```bash
# Chrome (padrão)
npm run cypress:run

# Firefox
npx cypress run --browser firefox

# Edge
npx cypress run --browser edge
```

### Modo Debug
```bash
npx cypress run --headed --no-exit
```

Deixa o browser aberto após completar.

---

## Cobertura de Testes

### Visualizar Coverage Report
```bash
npm test -- --coverage

# Abrir relatório HTML
open coverage/lcov-report/index.html
```

**Arquivo de configuração:** `jest.config.js`

**Thresholds atuais:**
```json
{
  "lines": 75,
  "functions": 75,
  "branches": 75,
  "statements": 75
}
```

### Verificar Cobertura por Arquivo
```bash
npm test -- --coverage --verbose
```

Mostra cobertura individual para cada arquivo testado.

### Gerar Coverage Badge
```bash
npm test -- --coverage --coverageReporters=text
```

---

## Estrutura de Testes

### Unit Tests (Jest)

**Localização:** `src/**/*.spec.ts`

**Tipos:**
- `src/services/**/*.spec.ts` - Service tests (HTTP, signals)
- `src/components/**/*.spec.ts` - Component tests (UI, events)
- `src/pipes/**/*.spec.ts` - Pipe tests (transformations)
- `src/directives/**/*.spec.ts` - Directive tests (DOM)

**Padrão de Nomenclatura:**
```
[feature].spec.ts
```

### E2E Tests (Cypress)

**Localização:** `cypress/e2e/**/*.cy.ts`

**Tipos:**
- User flows (onboarding, login, CRUD)
- Error scenarios (401, 404, 500, network)
- Integration tests (múltiplos componentes)

**Padrão de Nomenclatura:**
```
[feature-flow].cy.ts
```

---

## Teste Específico por Tipo

### Testes de Serviços
```bash
# Chat service
npm test -- chat.service.spec.ts

# Memory service
npm test -- memory.service.spec.ts

# User profile service
npm test -- user-profile.service.spec.ts

# Todos os serviços
npm test -- services/
```

### Testes de Componentes
```bash
# Chat component
npm test -- components/chat/chat.component.spec.ts

# Nutrition component
npm test -- components/nutrition/nutrition.component.spec.ts

# Dashboard
npm test -- components/dashboard/dashboard.component.spec.ts

# Todos os componentes
npm test -- components/
```

### Testes de Widgets
```bash
# Widget específico
npm test -- widget-macros-today.component.spec.ts

# Todos os widgets
npm test -- widgets/
```

### Testes E2E
```bash
# Onboarding flow
npx cypress run --spec "cypress/e2e/onboarding.cy.ts"

# Create nutrition
npx cypress run --spec "cypress/e2e/create-nutrition.cy.ts"

# Error scenarios
npx cypress run --spec "cypress/e2e/error-scenarios.cy.ts"

# Todos os E2E
npm run cypress:run
```

---

## Troubleshooting

### Jest Testes Falhando

**Problema: "spyOn is not defined"**
```
ReferenceError: spyOn is not defined
```
**Solução:**
```typescript
// Usar jest.spyOn ao invés de spyOn
jest.spyOn(object, 'method');
```

**Problema: "Cannot find module"**
```
Cannot find module './component'
```
**Solução:**
- Verificar se arquivo existe
- Verificar se está exportado
- Executar `npm install`

### Cypress Testes Falhando

**Problema: "cy.wait() timeout"**
```
CypressError: cy.wait() timed out waiting for the XHR request to 'POST /api/message'
```
**Solução:**
```typescript
// Aumentar timeout
cy.intercept('POST', '**/message', { delay: 1000 })
  .as('message');
cy.wait('@message', { timeout: 10000 });
```

**Problema: "Teste não encontra elemento"**
```
CypressError: Timed out retrying after 4000ms: cy.get() could not find a matching element
```
**Solução:**
```typescript
// Adicionar waits explícitos
cy.wait('@api');
cy.get('button').should('be.visible');
```

### Performance Lenta

**Problema: Testes rodam muito lento**
**Soluções:**
```bash
# Rodar apenas um arquivo
npm test -- chat.service.spec.ts

# Skip coverage geração
npm test -- --no-coverage

# Modo watch
npm test -- --watch
```

---

## Integração CI/CD

### GitHub Actions
```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Run Jest Tests
        run: cd frontend && npm test -- --coverage

      - name: Run Cypress Tests
        run: cd frontend && npm run cypress:run

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./frontend/coverage/lcov.info
```

---

## Boas Práticas

### ✅ DO

1. **Executar testes antes de fazer commit**
   ```bash
   npm test -- --coverage
   npm run cypress:run
   ```

2. **Usar factories para dados de teste**
   ```typescript
   import { MessageFactory } from '@test-utils/factories';
   const message = MessageFactory.create({ text: 'Hello' });
   ```

3. **Centralizar mocks**
   ```typescript
   import { ERROR_MOCKS } from 'cypress/support/mocks';
   cy.intercept('POST', '**/api', ERROR_MOCKS.serverError);
   ```

4. **Testar error scenarios**
   ```typescript
   it('should handle 500 error', () => {
     httpMock.expectOne('/api').flush(
       { detail: 'Error' },
       { status: 500, statusText: 'Error' }
     );
   });
   ```

5. **Usar helpers de teste**
   ```typescript
   import { createSignal, updateSignal } from '@test-utils/helpers';
   const signal = createSignal(initialValue);
   updateSignal(signal, newValue);
   ```

### ❌ DON'T

1. **Não mockear globalmente**
   ```typescript
   // ❌ Ruim
   jest.mock('./service');

   // ✅ Bom
   let mockService: Partial<Service>;
   ```

2. **Não usar sleep em testes**
   ```typescript
   // ❌ Ruim
   await new Promise(r => setTimeout(r, 1000));

   // ✅ Bom
   cy.wait('@api');
   ```

3. **Não chamar API real em testes**
   ```typescript
   // ❌ Ruim - sem mock
   cy.visit('/api/real-endpoint');

   // ✅ Bom - com mock
   cy.intercept('GET', '**/api/**', mockData);
   ```

---

## Recursos Adicionais

- [Jest Documentation](https://jestjs.io/)
- [Cypress Documentation](https://docs.cypress.io/)
- [Angular Testing Guide](https://angular.io/guide/testing)
- [Testing Library](https://testing-library.com/)

---

## Sumário de Comandos Úteis

```bash
# Desenvolvimento
npm test -- --watch                    # Jest watch mode
npm run cypress:open                   # Cypress interactive

# CI/CD
npm test -- --coverage                 # Jest com coverage
npm run cypress:run                    # Cypress headless

# Debug
npm test -- --verbose                  # Jest verbose
npx cypress run --headed               # Cypress com browser visível

# Específico
npm test -- services/                  # Apenas serviços
npm test -- components/chat/           # Apenas chat component
npx cypress run --spec "cypress/e2e/error-scenarios.cy.ts"
```

---

**Última Atualização:** 28 de Janeiro de 2026
**Total de Testes:** 877+
**Cobertura Target:** 80%+
**Backend Independence:** 100%
