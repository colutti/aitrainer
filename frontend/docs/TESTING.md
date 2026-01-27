# Testing Guide - AI Personal Trainer Frontend

Guia completo de testes para o frontend da aplicação AI Personal Trainer.

## Overview

Este projeto utiliza duas ferramentas de teste:

- **Jest**: Testes unitários para serviços, componentes, pipes e diretivas
- **Cypress**: Testes E2E completamente independentes do backend

## Rodando os Testes

### Testes Unitários

```bash
# Rodar todos os testes
npm test

# Rodar com cobertura
npm test -- --coverage

# Rodar testes de um arquivo específico
npm test -- auth.service.spec.ts

# Modo watch (reexecuta ao salvar)
npm test -- --watch

# Modo debug
node --inspect-brk node_modules/.bin/jest --runInBand
```

### Testes E2E (Cypress)

```bash
# Interface interativa (recomendado para desenvolvimento)
npm run cypress:open

# Modo headless (para CI/CD)
npm run cypress:run

# Rodar testes de um arquivo específico
npm run cypress:run -- --spec "cypress/e2e/login.cy.ts"

# Modo debug
npm run cypress:run -- --headed --no-exit
```

## Test Utilities

### Factories (Test Data Builders)

As factories criam dados de teste reutilizáveis e consistentes.

#### MessageFactory
```typescript
import { MessageFactory } from 'src/test-utils';

const message = MessageFactory.createAI('Olá!');
const messages = MessageFactory.createList(5, 'user');
const conversation = MessageFactory.createConversation();
```

#### WorkoutFactory
```typescript
import { WorkoutFactory } from 'src/test-utils';

const workout = WorkoutFactory.create();
const chest = WorkoutFactory.createChest();
const workouts = WorkoutFactory.createList(7, 'Peito');
```

#### NutritionFactory
```typescript
import { NutritionFactory } from 'src/test-utils';

const log = NutritionFactory.createLog();
const breakfast = NutritionFactory.createBreakfast();
const stats = NutritionFactory.createStats();
const logs = NutritionFactory.createLogList(14);
```

#### UserProfileFactory
```typescript
import { UserProfileFactory } from 'src/test-utils';

const user = UserProfileFactory.create();
const female = UserProfileFactory.createFemale();
const bulkGoal = UserProfileFactory.createBulkGoal();
```

#### TrainerFactory
```typescript
import { TrainerFactory } from 'src/test-utils';

const profile = TrainerFactory.create('atlas');
const option = TrainerFactory.createOption('luna', 'Luna');
const trainers = TrainerFactory.createAllTrainers();
```

### Helpers (Test Utilities)

#### SignalTestHelper
```typescript
import { SignalTestHelper } from 'src/test-utils';

// Criar signal
const sig = SignalTestHelper.createTestSignal(initialValue);

// Rastrear mudanças
const changes = SignalTestHelper.trackSignalChanges(sig);

// Aguardar mudança
await SignalTestHelper.waitForSignalChange(sig, val => val > 10);
```

#### HttpTestHelper
```typescript
import { HttpTestHelper } from 'src/test-utils';

const helper = new HttpTestHelper(httpMock);

// Esperar e responder
helper.expectAndRespond('GET', '/api/data', { data: [] });

// Simular erro
helper.expectAndError('POST', '/api/submit', 500);

// Erro de rede
helper.expectAndNetworkError('GET', '/api/data');

// Verificar corpo
helper.expectRequestBody('POST', '/api/submit', expectedBody);

// Verificar query params
helper.expectQueryParams('/api/data?page=1', { page: '1' });
```

#### ComponentTestHelper
```typescript
import { ComponentTestHelper } from 'src/test-utils';

const helper = new ComponentTestHelper(fixture);

// Encontrar elementos
const element = helper.findByCss('.button');
const elements = helper.findAllByCss('.item');

// Interações
helper.click('.button');
helper.setInputValue('input', 'new value');
helper.triggerEvent('.component', 'customEvent', { data: 'test' });

// Verificações
helper.hasElement('.button'); // true
helper.getTextContent('.title'); // 'Hello'
helper.hasClass('.button', 'active'); // true

// Aguardar
await helper.waitFor(() => helper.hasElement('.loaded'));
await helper.stabilize(); // Detect changes + whenStable
```

## Padrões de Teste

### Padrão: Testes de Serviços

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { XxxService } from './xxx.service';
import { HttpTestHelper } from 'src/test-utils';

describe('XxxService', () => {
  let service: XxxService;
  let httpMock: HttpTestingController;
  let httpHelper: HttpTestHelper;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        XxxService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(XxxService);
    httpMock = TestBed.inject(HttpTestingController);
    httpHelper = new HttpTestHelper(httpMock);
  });

  afterEach(() => {
    httpHelper.verifyNoPendingRequests();
  });

  describe('getData()', () => {
    it('should fetch data successfully', async () => {
      const mockData = [{ id: 1, name: 'Test' }];

      const promise = service.getData();
      httpHelper.expectAndRespond('GET', /api\/data/, mockData);

      const result = await promise;
      expect(result).toEqual(mockData);
      expect(service.data()).toEqual(mockData);
      expect(service.isLoading()).toBe(false);
    });

    it('should handle 500 error', async () => {
      const promise = service.getData();
      httpHelper.expectAndError('GET', /api\/data/, 500);

      const result = await promise;
      expect(result).toEqual([]); // fallback
    });
  });
});
```

**Casos de Teste Obrigatórios:**
- ✅ Service creation
- ✅ Signal initialization
- ✅ Happy path (HTTP success)
- ✅ Error handling (404, 500, network)
- ✅ Signal updates após operação
- ✅ Loading state
- ✅ Edge cases (null, empty response)

### Padrão: Testes de Componentes

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { XxxComponent } from './xxx.component';
import { XxxService } from './xxx.service';
import { ComponentTestHelper } from 'src/test-utils';

describe('XxxComponent', () => {
  let component: XxxComponent;
  let fixture: ComponentFixture<XxxComponent>;
  let helper: ComponentTestHelper;
  let mockService: Partial<XxxService>;

  beforeEach(async () => {
    mockService = {
      data: signal([]),
      isLoading: signal(false),
      getData: jest.fn().mockResolvedValue([])
    };

    await TestBed.configureTestingModule({
      imports: [XxxComponent],
      providers: [{ provide: XxxService, useValue: mockService }]
    }).compileComponents();

    fixture = TestBed.createComponent(XxxComponent);
    helper = new ComponentTestHelper(fixture);
    component = fixture.componentInstance;
  });

  it('should load data on init', () => {
    fixture.detectChanges();
    expect(mockService.getData).toHaveBeenCalled();
  });

  it('should display data in template', () => {
    mockService.data!.set([{ id: 1, name: 'Test' }]);
    fixture.detectChanges();

    expect(helper.hasElement('.item')).toBe(true);
    expect(helper.getTextContent('.item')).toContain('Test');
  });

  it('should call service on button click', () => {
    fixture.detectChanges();
    helper.click('.submit-button');

    expect(mockService.getData).toHaveBeenCalled();
  });
});
```

**Casos de Teste Obrigatórios:**
- ✅ Component creation
- ✅ ngOnInit behavior
- ✅ Template rendering (data, empty, loading, error)
- ✅ User interactions (click, input)
- ✅ Service calls
- ✅ Signal updates
- ✅ Computed signals

### Padrão: Testes de Pipes

```typescript
import { AppXxxPipe } from './xxx.pipe';

describe('AppXxxPipe', () => {
  let pipe: AppXxxPipe;

  beforeEach(() => {
    pipe = new AppXxxPipe();
  });

  it('should transform valid input', () => {
    expect(pipe.transform('input')).toBe('expected');
  });

  it('should handle null value', () => {
    expect(pipe.transform(null)).toBeNull();
  });

  it('should handle different formats', () => {
    expect(pipe.transform(value, 'format1')).toBe(expected1);
    expect(pipe.transform(value, 'format2')).toBe(expected2);
  });
});
```

### Padrão: Testes de Diretivas

```typescript
import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { XxxDirective } from './xxx.directive';
import { ComponentTestHelper } from 'src/test-utils';

@Component({
  template: `<input appXxx />`
})
class TestComponent {}

describe('XxxDirective', () => {
  let fixture: ComponentFixture<TestComponent>;
  let helper: ComponentTestHelper;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [XxxDirective, TestComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TestComponent);
    helper = new ComponentTestHelper(fixture);
  });

  it('should handle valid input', () => {
    helper.setInputValue('input', 'valid');
    expect(helper.getTextContent('input')).toBe('valid');
  });

  it('should prevent invalid input', () => {
    const event = new KeyboardEvent('keydown', { key: 'invalid' });
    helper.triggerEvent('input', 'keydown', event);
    expect(event.defaultPrevented).toBe(true);
  });
});
```

## Mocks do Cypress

### Usando Mocks Comuns

```typescript
import { COMMON_MOCKS, ERROR_MOCKS, CHAT_MOCKS } from '../support/mocks';

describe('Dashboard', () => {
  it('should load dashboard with all stats', () => {
    cy.mockLogin({
      intercepts: {
        '**/workout/stats': { body: COMMON_MOCKS.workoutStats },
        '**/nutrition/stats': { body: COMMON_MOCKS.nutritionStats },
        '**/metabolism/summary*': { body: COMMON_MOCKS.metabolismSummary }
      }
    });

    cy.visit('/dashboard');
    cy.contains('Stats').should('be.visible');
  });

  it('should handle 500 error gracefully', () => {
    cy.mockLogin({
      intercepts: {
        '**/workout/stats': ERROR_MOCKS.serverError
      }
    });

    cy.visit('/dashboard');
    cy.contains('Erro ao carregar').should('be.visible');
  });
});
```

### Criando Mocks Customizados

```typescript
import { createErrorResponse, createValidationError } from '../support/mocks';

it('should show validation error', () => {
  cy.mockLogin({
    intercepts: {
      'POST **/user/register': createValidationError('email', 'Email inválido')
    }
  });

  cy.visit('/register');
  cy.get('input[name="email"]').type('invalid');
  cy.get('button').click();
  cy.contains('Email inválido').should('be.visible');
});
```

## Cobertura de Testes

### Gerar Relatório de Cobertura

```bash
npm test -- --coverage

# Abrir relatório em HTML
open coverage/lcov-report/index.html
```

### Métricas por Arquivo

O relatório mostra:
- **FN**: Funções cobertas vs. total
- **DA**: Linhas de código executadas
- **BR**: Branches cobertos
- **LN**: Linhas de código testadas

### CI/CD

Os testes rodam automaticamente em cada push:

```bash
# GitHub Actions verifica:
# 1. npm test (cobertura)
# 2. npm run cypress:run (E2E)
# 3. Cobertura >= 95%
```

## Best Practices

1. **AAA Pattern (Arrange-Act-Assert)**
   ```typescript
   // Arrange
   const data = MessageFactory.createList(5);
   mockService.data.set(data);

   // Act
   fixture.detectChanges();

   // Assert
   expect(component.messageCount()).toBe(5);
   ```

2. **Use Factories para Dados de Teste**
   - Não crie dados inline
   - Reutilize factories em múltiplos testes
   - Crie variações específicas conforme necessário

3. **Mock Serviços, não HTTP**
   - Em testes de componente: mock o serviço (Partial<T>)
   - Em testes de serviço: mock o HTTP (HttpTestingController)
   - Nunca teste o componente contra um serviço real

4. **Cypress: 100% Independente**
   - Sempre use `cy.intercept()` para mockar respostas
   - Mocks devem estar prontos ANTES de `cy.visit()`
   - Nunca conecte a um backend real nos testes

5. **Limpar Estado Entre Testes**
   ```typescript
   afterEach(() => {
     httpMock.verify();
     localStorage.clear();
     sessionStorage.clear();
   });
   ```

6. **Testar Edge Cases**
   - null/undefined
   - Empty responses
   - Conflicting data
   - Network errors
   - Validation errors

## Troubleshooting

### HttpTestingController - Requisição Não Encontrada

```typescript
// ❌ Errado
const req = httpMock.expectOne('/api/data');

// ✅ Correto (com regex)
const req = httpMock.expectOne(req => req.url.includes('/api/data'));
```

### Signals não Atualizam em Teste

```typescript
// Certifique-se de chamar fixture.detectChanges() após modificar signals
mockService.data.set([...]);
fixture.detectChanges(); // Necessário!
```

### Cypress - Elemento Não Encontrado

```typescript
// Use cy.visit() APÓS setupar os mocks
cy.mockLogin({ intercepts: { ... } }); // Setup
cy.visit('/dashboard');                 // Visita
```

## Resources

- [Angular Testing Guide](https://angular.io/guide/testing)
- [Jest Documentation](https://jestjs.io/)
- [Cypress Documentation](https://docs.cypress.io/)
- `src/test-utils/` - Test utilities
- `cypress/support/mocks/` - Cypress mocks
