/// <reference types="cypress" />

Cypress.Commands.add('login', (email, password) => {
  cy.visit('/');
  cy.get('app-login').should('be.visible');
  cy.get('input#email').clear().type(email);
  cy.get('input#password').clear().type(password);
  cy.get('button[type="submit"]').contains('Entrar').click();
  
  // Wait for the login component to disappear and the sidebar to appear
  cy.get('app-login', { timeout: 10000 }).should('not.exist');
  cy.get('app-sidebar').should('be.visible');
});
