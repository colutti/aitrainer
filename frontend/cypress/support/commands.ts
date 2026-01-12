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
