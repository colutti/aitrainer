import { setupCommonIntercepts } from './intercepts';

/// <reference types="cypress" />

Cypress.Commands.add('login', (email, password) => {
  cy.visit('/');
  cy.get('app-login').should('be.visible');
  cy.get('input#email', { timeout: 10000 }).clear().type(email);
  cy.get('input#password').clear().type(password);
  cy.get('button[type="submit"]').contains('Entrar').click();
  
  // Wait for the login component to disappear and the sidebar to appear
  cy.get('app-login', { timeout: 15000 }).should('not.exist');
  cy.get('app-sidebar', { timeout: 15000 }).should('be.visible');
  
  // Ensure we land on dashboard and it's stable
  cy.get('app-dashboard', { timeout: 15000 }).should('be.visible');
  cy.wait(500); // Give Angular a moment to settle re-renders
});

Cypress.Commands.add('loginDirect', (email, password) => {
  cy.request('POST', '/api/user/login', { email, password }).then((response) => {
    expect(response.status).to.eq(200);
    localStorage.setItem('jwt_token', response.body.token);
  });
});

// Helper to set a properly structured fake JWT token (3 segments)
// This prevents backend "Not enough segments" errors
Cypress.Commands.add('setFakeJWT', () => {
  // Create a valid JWT structure: header.payload.signature
  // Using base64-encoded dummy data
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ 
    email: 'cypress_user@test.com', 
    exp: Math.floor(Date.now() / 1000) + 3600 
  }));
  const signature = btoa('fake-signature');
  const fakeJWT = `${header}.${payload}.${signature}`;
  
  window.localStorage.setItem('jwt_token', fakeJWT);
});
Cypress.Commands.add('mockLogin', (options: any = {}) => {
  const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImN5cHJlc3NfdXNlckB0ZXN0LmNvbSIsImV4cCI6OTk5OTk5OTk5OX0.fake';
  
  // Setup common mocks before anything else
  setupCommonIntercepts();
  
  if (options.intercepts) {
    Object.entries(options.intercepts).forEach(([key, val]: [string, any]) => {
      const parts = key.split(' ');
      const method = parts.length === 2 ? parts[0] : 'GET';
      const url = parts.length === 2 ? parts[1] : key;
      
      let response = val;
      let alias = null;
      
      if (val && typeof val === 'object' && (val.body !== undefined || val.statusCode !== undefined)) {
        response = { ...val };
        alias = val.alias;
        delete response.alias;
      }
      
      const intercept = cy.intercept(method as any, url, response);
      if (alias) {
        intercept.as(alias);
      }
    });
  }
  
  // Speed up by preventing unnecessary font/asset loads if they are slow
  cy.intercept('GET', '**/assets/**', { statusCode: 200, body: '' }).as('assets');

  cy.visit('/', {
    timeout: 30000,
    onBeforeLoad: (win) => {
      win.localStorage.clear();
      win.localStorage.setItem('jwt_token', mockToken);
    }
  });
  
  // Use much shorter timeouts. 5s is plenty for mocks.
  cy.get('app-sidebar', { timeout: 15000 }).should('exist');
  
  // Don't wait for app-dashboard specifically, as we might navigate away quickly
  // or it might be replaced by other views. Sidebar is enough to prove we are "in".
});
