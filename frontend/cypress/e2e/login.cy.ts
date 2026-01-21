import { setupCommonIntercepts } from '../support/intercepts';

describe('Login Flow', () => {
  beforeEach(() => {
    // Start from the root, which should redirect to login if not authenticated
    cy.visit('/');
  });

  it('should display the login page', () => {
    cy.get('app-login').should('be.visible');
  });

  it('should have empty credentials by default', () => {
    // The login form should start empty
    cy.get('input#email').should('have.value', '');
    cy.get('input#password').should('have.value', '');
  });

  it('should show an error for invalid credentials', () => {
    // Mock login failure
    cy.intercept('POST', '**/user/login', {
      statusCode: 401,
      body: { detail: 'Credenciais inválidas' }
    }).as('loginFail');

    cy.get('input#email').clear().type('invalid@email.com');
    cy.get('input#password').clear().type('wrongpassword');
    cy.get('button[type="submit"]').contains('Entrar').click();

    cy.wait('@loginFail');
    cy.contains('Credenciais inválidas. Tente novamente.').should('be.visible');
  });

  it('should log in a user successfully and redirect to dashboard', () => {
    // Setup mocks for dashboard data that loads after login
    setupCommonIntercepts();

    // Mock successful login (Must be defined AFTER setupCommonIntercepts to override catch-all if catch-all is buggy, 
    // OR if setupCommonIntercepts has its own defaults. Actually, explicit routes usually take precedence in Cypress 
    // regardless of order IF they are more specific, but "specific" is tricky. Safe bet: Define specific AFTER general.)
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImN5cHJlc3NfdXNlckB0ZXN0LmNvbSIsImV4cCI6OTk5OTk5OTk5OX0.fake' }
    }).as('loginSuccess');

    cy.get('input#email').clear().type('cypress_user@test.com');
    cy.get('input#password').clear().type('CorrectPassword');
    cy.get('button[type="submit"]').contains('Entrar').click();

    cy.wait('@loginSuccess');

    // After login, wait for URL to change first (more reliable indicator of routing)
    cy.url({ timeout: 15000 }).should('not.include', 'login');
    
    // Then check for UI changes
    cy.get('app-login', { timeout: 15000 }).should('not.exist');
    cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');
    cy.get('app-dashboard', { timeout: 15000 }).should('be.visible');
  });

  it('should log out the user', () => {
    // Use mock login to start from a logged-in state
    cy.mockLogin();

    // Reload is NOT needed with mockLogin as it starts fresh
    cy.get('app-sidebar').should('be.visible');

    // Intercept POST logout call
    cy.intercept('POST', '*logout*', { statusCode: 200, body: { message: 'Logged out successfully' } }).as('logout');

    // Find and click the logout button in the sidebar. Scroll into view and force click due to overflow.
    cy.get('app-sidebar button').contains('Sair').scrollIntoView().click({ force: true });

    // After logout, it should redirect back to the login page
    cy.get('app-login', { timeout: 10000 }).should('be.visible');
    cy.get('app-sidebar').should('not.exist');
  });
});

