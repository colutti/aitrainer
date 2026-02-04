import { setupCommonIntercepts } from '../support/intercepts';

describe('Token Expiration - Automatic Logout', () => {
  /**
   * Test Suite para validar que a sessão expira automaticamente
   * sem necessidade de interação do usuário com a API.
   *
   * Cenários testados:
   * 1. Login bem-sucedido com token válido
   * 2. Token expira automaticamente após o tempo configurado
   * 3. Usuário é redirecionado para login sem clicar em nada
   * 4. localStorage é limpo
   * 5. Login subsequente funciona normalmente
   */

  beforeEach(() => {
    // Clear any existing state
    cy.clearLocalStorage();
    cy.visit('/', { timeout: 60000 });
  });

  it('should display login page when not authenticated', () => {
    cy.get('app-login', { timeout: 20000 }).should('be.visible');
    cy.get('app-sidebar').should('not.exist');
  });

  it('should login successfully and display dashboard', () => {
    setupCommonIntercepts();

    // Mock login endpoint
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: {
        token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjo5OTk5OTk5OTk5fQ.fake'
      }
    }).as('loginSuccess');

    // Perform login
    cy.get('input#email', { timeout: 10000 }).clear().type('test@test.com');
    cy.get('input#password').clear().type('password123');
    cy.get('button[type="submit"]').contains('Entrar').click();

    // Wait for login success
    cy.wait('@loginSuccess');

    // Verify dashboard is visible
    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');
    cy.get('app-dashboard', { timeout: 15000 }).should('exist');

    // Verify token is stored
    cy.window().then((win) => {
      expect(win.localStorage.getItem('jwt_token')).to.exist;
    });
  });

  it('should automatically logout when token expires', () => {
    setupCommonIntercepts();

    // 1. Login with a token that expires in 2 seconds
    const expireTime = Math.floor(Date.now() / 1000) + 2;
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: 'test@test.com', exp: expireTime }));
    const mockToken = `${header}.${payload}.fake`;

    cy.visit('/', {
      timeout: 30000,
      onBeforeLoad: (win) => {
        win.localStorage.clear();
        win.localStorage.setItem('jwt_token', mockToken);
      }
    });

    // 2. Wait for app to be authenticated
    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');
    cy.get('app-dashboard').should('exist');

    // 3. Wait for token to expire (2s expiration + buffer - 5s = ~0s, so it should fire almost immediately)
    // Actually, the timer schedules for expiration - 5000ms, so with 2s expiration,
    // it fires immediately. Let's wait a bit to be safe.
    cy.wait(1500);

    // 4. Check that console shows expiration message (optional but helpful for debugging)
    cy.window().then((win) => {
      // The app should have called logout
      // which clears localStorage
      expect(win.localStorage.getItem('jwt_token')).to.be.null;
    });

    // 5. Verify that login page is displayed (automatic logout happened)
    cy.get('app-login', { timeout: 10000 }).should('be.visible');
    cy.get('app-sidebar').should('not.exist');
  });

  it('should automatically logout on token expiration without user interaction', () => {
    setupCommonIntercepts();

    // Setup: Login with a short-lived token (expires in 3 seconds)
    const expireTime = Math.floor(Date.now() / 1000) + 3;
    const shortLivedToken = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' })) +
      '.' +
      btoa(JSON.stringify({ sub: 'test@test.com', exp: expireTime })) +
      '.fake';

    cy.visit('/', {
      timeout: 30000,
      onBeforeLoad: (win) => {
        win.localStorage.clear();
        win.localStorage.setItem('jwt_token', shortLivedToken);
      }
    });

    // Verify authenticated state
    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');

    // IMPORTANT: Do NOT interact with the app
    // Just wait for automatic logout

    // The timer should fire ~-2s from now (3s expiration - 5s buffer = negative, so immediately)
    // Let's wait a bit longer to account for timing
    cy.wait(2000);

    // Verify automatic logout happened
    cy.get('app-login', { timeout: 10000 }).should('be.visible');
    cy.get('app-sidebar').should('not.exist');

    // Verify localStorage was cleared
    cy.window().then((win) => {
      expect(win.localStorage.getItem('jwt_token')).to.be.null;
    });
  });

  it('should allow re-login after automatic logout', () => {
    setupCommonIntercepts();

    // 1. Login with short-lived token
    const expireTime = Math.floor(Date.now() / 1000) + 2;
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: 'test@test.com', exp: expireTime }));
    const shortLivedToken = `${header}.${payload}.fake`;

    cy.visit('/', {
      timeout: 30000,
      onBeforeLoad: (win) => {
        win.localStorage.clear();
        win.localStorage.setItem('jwt_token', shortLivedToken);
      }
    });

    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');

    // 2. Wait for automatic logout
    cy.wait(2000);
    cy.get('app-login', { timeout: 10000 }).should('be.visible');

    // 3. Login again with new token
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: {
        token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjo5OTk5OTk5OTk5fQ.fake'
      }
    }).as('secondLogin');

    cy.get('input#email', { timeout: 10000 }).clear().type('test@test.com');
    cy.get('input#password').clear().type('password123');
    cy.get('button[type="submit"]').contains('Entrar').click();

    cy.wait('@secondLogin');

    // 4. Verify re-authentication works
    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');
    cy.get('app-dashboard', { timeout: 15000 }).should('exist');
  });

  it('should not logout when token is still valid', () => {
    setupCommonIntercepts();

    // Login with a long-lived token (expires in 1 hour)
    const expireTime = Math.floor(Date.now() / 1000) + 3600;
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: 'test@test.com', exp: expireTime }));
    const longLivedToken = `${header}.${payload}.fake`;

    cy.visit('/', {
      timeout: 30000,
      onBeforeLoad: (win) => {
        win.localStorage.clear();
        win.localStorage.setItem('jwt_token', longLivedToken);
      }
    });

    // Verify authenticated
    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');

    // Wait a few seconds - should NOT logout because token is still valid
    cy.wait(3000);

    // Verify still authenticated
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-login').should('not.exist');

    // Token should still be in localStorage
    cy.window().then((win) => {
      expect(win.localStorage.getItem('jwt_token')).to.exist;
    });
  });


  it('should handle 401 error with expired token as fallback', () => {
    setupCommonIntercepts();

    // 1. Login successfully
    cy.mockLogin({
      intercepts: {
        'POST /api/user/login': {
          statusCode: 200,
          body: {
            token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjo5OTk5OTk5OTk5fQ.fake'
          },
          alias: 'login'
        }
      }
    });

    // 2. Setup an endpoint to return 401
    cy.intercept('GET', '**/user/profile', {
      statusCode: 401,
      body: { detail: 'Token expired' }
    }).as('profile401');

    // 3. Trigger the API call that will fail
    cy.get('app-sidebar button').contains('Meu Perfil').click({ force: true });

    // 4. Wait for 401 response
    cy.wait('@profile401');

    // 5. Error interceptor should also trigger logout
    // Verify we're back on login page
    cy.get('app-login', { timeout: 10000 }).should('be.visible');
  });

  it('should clear localStorage on automatic logout', () => {
    setupCommonIntercepts();

    // Login with expiring token
    const expireTime = Math.floor(Date.now() / 1000) + 2;
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ sub: 'test@test.com', exp: expireTime }));
    const token = `${header}.${payload}.fake`;

    cy.visit('/', {
      timeout: 30000,
      onBeforeLoad: (win) => {
        win.localStorage.clear();
        win.localStorage.setItem('jwt_token', token);
      }
    });

    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');

    // Verify token exists before expiration
    cy.window().then((win) => {
      expect(win.localStorage.getItem('jwt_token')).to.equal(token);
    });

    // Wait for expiration
    cy.wait(2000);

    // Verify localStorage was cleared
    cy.window().then((win) => {
      expect(win.localStorage.getItem('jwt_token')).to.be.null;
    });

    // Verify login page is shown
    cy.get('app-login', { timeout: 10000 }).should('be.visible');
  });
});
