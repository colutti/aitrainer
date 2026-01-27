import { COMMON_MOCKS } from '../support/mocks';

describe('Create Nutrition Log Flow', () => {
  beforeEach(() => {
    cy.mockLogin();
    cy.visit('/nutrition/log');
  });

  it('should log nutrition entry', () => {
    cy.intercept('POST', '**/nutrition/log', { body: { id: '123', date: new Date() } }).as('logNutrition');

    cy.get('input[name="date"]').type('27/01/2026');
    cy.get('select[name="mealType"]').select('Café da Manhã');
    cy.get('input[name="description"]').type('2 ovos com pão');
    cy.get('input[name="calories"]').type('300');
    cy.get('input[name="protein"]').type('20');
    cy.get('input[name="carbs"]').type('30');
    cy.get('input[name="fat"]').type('10');

    cy.get('button').contains('Registrar').click();
    cy.wait('@logNutrition');

    cy.contains('Nutrição registrada com sucesso').should('be.visible');
  });

  it('should validate calorie input', () => {
    cy.get('input[name="calories"]').type('abc');
    cy.get('button').contains('Registrar').should('be.disabled');
  });

  it('should calculate macros if provided', () => {
    cy.get('input[name="calories"]').type('2000');
    cy.get('input[name="protein"]').type('150');
    cy.get('input[name="carbs"]').type('200');
    cy.get('input[name="fat"]').type('70');

    // Verify macro percentages are displayed
    cy.get('[data-test="protein-percent"]').should('be.visible');
    cy.get('[data-test="carbs-percent"]').should('be.visible');
  });

  it('should allow quick meal templates', () => {
    cy.get('button').contains('Café da Manhã').click();

    // Should populate typical breakfast macros
    cy.get('input[name="calories"]').should('have.value', '500');
    cy.get('input[name="description"]').should('have.value', 'Café da manhã típico');
  });

  it('should show calorie and macro summary', () => {
    cy.get('input[name="calories"]').type('2000');
    cy.get('input[name="protein"]').type('150');
    cy.get('input[name="carbs"]').type('200');
    cy.get('input[name="fat"]').type('70');

    cy.get('[data-test="macro-summary"]').should('contain', '2000');
  });

  it('should handle server error', () => {
    cy.intercept('POST', '**/nutrition/log', { statusCode: 500, body: { detail: 'Server error' } }).as('error');

    cy.get('input[name="date"]').type('27/01/2026');
    cy.get('input[name="calories"]').type('300');
    cy.get('button').contains('Registrar').click();

    cy.wait('@error');
    cy.contains('Erro ao registrar').should('be.visible');
  });

  it('should clear form after success', () => {
    cy.intercept('POST', '**/nutrition/log', { body: { id: '123' } }).as('logNutrition');

    cy.get('input[name="date"]').type('27/01/2026');
    cy.get('input[name="calories"]').type('300');
    cy.get('button').contains('Registrar').click();

    cy.wait('@logNutrition');
    cy.get('input[name="calories"]').should('have.value', '');
  });
});
