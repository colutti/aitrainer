# Token Expiration E2E Tests - Cypress

## Visão Geral

Testes E2E (end-to-end) para validar a funcionalidade de detecção automática de expiração de sessão usando Cypress.

**Arquivo:** `frontend/cypress/e2e/token-expiration.cy.ts`

## Estratégia de Testes

### Mocking do Backend

Todos os testes usam `cy.intercept()` para mockar requisições HTTP do backend:

```typescript
cy.intercept('POST', '**/user/login', {
  statusCode: 200,
  body: { token: 'mocked-token' }
}).as('loginSuccess');
```

**Benefícios:**
- ✅ Testes rápidos (sem servidor real)
- ✅ Determinísticos (sem flakiness)
- ✅ Isolados (não afetam dados reais)
- ✅ Repetivelmente executáveis

### Setup Comum

```typescript
beforeEach(() => {
  cy.clearLocalStorage();
  cy.visit('/', { timeout: 60000 });
});
```

Cada teste começa com:
1. localStorage limpo
2. Página recarregada
3. Estado inicial limpo

## Testes Implementados

### 1. Login Page Display (455ms)
**Cenário:** Usuário não autenticado

```typescript
it('should display login page when not authenticated', () => {
  cy.get('app-login', { timeout: 20000 }).should('be.visible');
  cy.get('app-sidebar').should('not.exist');
});
```

**Validação:** Login page é exibido quando não há token

---

### 2. Successful Login (973ms)
**Cenário:** Usuário faz login com credenciais válidas

```typescript
it('should login successfully and display dashboard', () => {
  cy.intercept('POST', '**/user/login', {
    body: { token: '...' }
  }).as('loginSuccess');

  cy.get('input#email').type('test@test.com');
  cy.get('input#password').type('password123');
  cy.get('button[type="submit"]').click();

  cy.wait('@loginSuccess');
  cy.get('app-sidebar').should('be.visible');
  cy.get('app-dashboard').should('exist');
});
```

**Validação:**
- ✅ Login endpoint chamado
- ✅ Token armazenado em localStorage
- ✅ Dashboard renderizado

---

### 3. Automatic Logout on Token Expiration (1784ms)
**Cenário:** Token expira enquanto usuário está navegando

```typescript
it('should automatically logout when token expires', () => {
  const expireTime = Math.floor(Date.now() / 1000) + 2;
  const mockToken = `${header}.${payload}.fake`;

  cy.visit('/', {
    onBeforeLoad: (win) => {
      win.localStorage.setItem('jwt_token', mockToken);
    }
  });

  cy.get('app-sidebar').should('be.visible');
  cy.wait(1500); // Aguardar expiração

  cy.get('app-login').should('be.visible'); // Logout automático
  cy.window().then((win) => {
    expect(win.localStorage.getItem('jwt_token')).to.be.null;
  });
});
```

**Validação:**
- ✅ Token expira sem interação
- ✅ TokenExpirationService detecta expiração
- ✅ Logout automático dispara
- ✅ localStorage é limpo
- ✅ Login page é renderizada

---

### 4. Logout Without User Interaction (2280ms)
**Cenário:** Token expira **SEM NENHUM CLIQUE DO USUÁRIO**

```typescript
it('should automatically logout on token expiration without user interaction', () => {
  // Setup token que expira em 3s
  const expireTime = Math.floor(Date.now() / 1000) + 3;
  // ... visit com token ...

  cy.get('app-sidebar').should('be.visible');

  // IMPORTANTE: NÃO interagir com a app
  cy.wait(2000);

  // Logout deve ter acontecido automaticamente
  cy.get('app-login').should('be.visible');
});
```

**Validação:**
- ✅ Logout ocorre **proativamente**
- ✅ **Não depende** de cliques em botões
- ✅ **Não depende** de requisições HTTP

---

### 5. Re-login After Automatic Logout (3078ms)
**Cenário:** Usuário consegue fazer login novamente após expiração

```typescript
it('should allow re-login after automatic logout', () => {
  // 1. Login com token que expira em 2s
  // 2. Aguardar logout automático
  cy.get('app-login').should('be.visible');

  // 3. Login novamente
  cy.intercept('POST', '**/user/login', {
    body: { token: '...' }
  }).as('secondLogin');

  cy.get('input#email').type('test@test.com');
  cy.get('input#password').type('password123');
  cy.get('button[type="submit"]').click();

  cy.wait('@secondLogin');
  cy.get('app-sidebar').should('be.visible');
});
```

**Validação:**
- ✅ Logout automático não prejudica login posterior
- ✅ AuthService está funcional depois

---

### 6. Long-lived Token (3301ms)
**Cenário:** Token com validade longa **NÃO** expira prematuramente

```typescript
it('should not logout when token is still valid', () => {
  // Token expira em 1 hora
  const expireTime = Math.floor(Date.now() / 1000) + 3600;
  // ... visit com token ...

  cy.get('app-sidebar').should('be.visible');
  cy.wait(3000); // Aguardar alguns segundos

  // Deve estar AINDA logado
  cy.get('app-sidebar').should('be.visible');
  cy.get('app-login').should('not.exist');
});
```

**Validação:**
- ✅ Timer **não** dispara para tokens válidos
- ✅ Logout não é precipitado

---

### 7. 401 Error Fallback (696ms)
**Cenário:** ErrorInterceptor também faz logout em 401

```typescript
it('should handle 401 error with expired token as fallback', () => {
  cy.mockLogin();

  // Setup 401 error
  cy.intercept('GET', '**/user/profile', {
    statusCode: 401,
    body: { detail: 'Token expired' }
  }).as('profile401');

  cy.get('app-sidebar button').contains('Meu Perfil').click();
  cy.wait('@profile401');

  // ErrorInterceptor dispara logout
  cy.get('app-login').should('be.visible');
});
```

**Validação:**
- ✅ Defesa em profundidade: ErrorInterceptor também detecta 401
- ✅ TokenExpirationService + ErrorInterceptor trabalham juntos

---

### 8. localStorage Cleanup (2257ms)
**Cenário:** localStorage é limpo após logout automático

```typescript
it('should clear localStorage on automatic logout', () => {
  // ... setup com token que expira ...

  cy.window().then((win) => {
    expect(win.localStorage.getItem('jwt_token')).to.equal(token);
  });

  cy.wait(2000); // Aguardar expiração

  cy.window().then((win) => {
    expect(win.localStorage.getItem('jwt_token')).to.be.null;
  });

  cy.get('app-login').should('be.visible');
});
```

**Validação:**
- ✅ Token é removido de localStorage
- ✅ Nenhum token inválido fica armazenado

---

## Execução dos Testes

### Pré-requisitos

1. Frontend deve estar rodando:
```bash
npm run dev
```

2. Cypress instalado:
```bash
npm install cypress
```

### Executar Testes

**Todos os testes de token expiration:**
```bash
npm run cypress:run -- --spec 'cypress/e2e/token-expiration.cy.ts'
```

**Modo interativo (visualizar execução):**
```bash
npm run cypress:open
```
Selecionar `token-expiration.cy.ts` na interface

**Todos os testes E2E:**
```bash
npm run cypress:extended
```

### Resultado Esperado

```
✔  token-expiration.cy.ts                   00:15        8        8        -        -        -
✔  All specs passed!                        00:15        8        8        -        -        -
```

## Cobertura de Testes

| Cenário | Status | Tempo |
|---------|--------|-------|
| Login page display | ✅ | 455ms |
| Successful login | ✅ | 973ms |
| Auto-logout on expiration | ✅ | 1784ms |
| No user interaction needed | ✅ | 2280ms |
| Re-login after logout | ✅ | 3078ms |
| Long-lived token handling | ✅ | 3301ms |
| 401 Fallback (ErrorInterceptor) | ✅ | 696ms |
| localStorage cleanup | ✅ | 2257ms |
| **TOTAL** | **8/8** | **~15s** |

## Mocking Strategy

### Tokens Reais Criados em Tempo de Execução

```typescript
const expireTime = Math.floor(Date.now() / 1000) + 2; // Expira em 2s
const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
const payload = btoa(JSON.stringify({ sub: 'test@test.com', exp: expireTime }));
const mockToken = `${header}.${payload}.fake`;
```

### cy.intercept() Patterns

**Login:**
```typescript
cy.intercept('POST', '**/user/login', {
  statusCode: 200,
  body: { token: 'token-string' }
}).as('loginSuccess');
```

**User Info:**
```typescript
cy.intercept('GET', '**/user/me', {
  statusCode: 200,
  body: { email: 'test@test.com', role: 'user' }
}).as('userMe');
```

**Error (401):**
```typescript
cy.intercept('GET', '**/user/profile', {
  statusCode: 401,
  body: { detail: 'Token expired' }
}).as('profile401');
```

## Recursos Testados

- ✅ `TokenExpirationService` - Decodificação e agendamento
- ✅ `AuthService` - Login, logout, loadUserInfo
- ✅ `AppComponent` - Effect de logout automático
- ✅ `ErrorInterceptor` - Fallback para 401
- ✅ `localStorage` - Armazenamento e limpeza de token
- ✅ UI Components - Login page, sidebar, dashboard

## Notas Importantes

1. **Sem servidor backend necessário** - Todos os testes mocka requisições
2. **Testes determinísticos** - Sempre passam com mesmos inputs
3. **Rápidos** - ~15 segundos para 8 testes (vs minutos com servidor real)
4. **Isolados** - Não afetam dados reais ou outros usuários
5. **Repetíveis** - Podem ser executados infinitas vezes
6. **CI/CD Ready** - Integração com GitHub Actions, Jenkins, etc

## Troubleshooting

### Teste falhando com "Timed out retrying"
- Aumentar timeout em `cypress.config.ts`
- Verificar se frontend está rodando em http://localhost:3000

### localStorage não limpo entre testes
- Verificar `beforeEach()` com `cy.clearLocalStorage()`

### Token inválido
- Verificar formato do JWT (header.payload.signature)
- Usar helper `btoa()` para base64 encoding

## Próximas Melhorias

1. **Testes de performance** - Tempo de resposta esperado
2. **Testes de navegador múltiplo** - Chrome, Firefox, Safari
3. **Testes de rede lenta** - Simular latência
4. **Testes paralelos** - Executar múltiplos testes em paralelo
5. **Visual regression** - Comparar screenshots entre versões
