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
