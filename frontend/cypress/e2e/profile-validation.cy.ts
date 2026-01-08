describe('Form Validation Flow', () => {
  beforeEach(() => {
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button').contains('Meu Perfil').should('be.visible').click();
    cy.get('app-user-profile').should('be.visible');
  });

  it('should display validation errors from the backend when submitting invalid data', () => {
    // Intercept the update call to check the response
    cy.intercept('POST', '**/user/update_profile').as('updateProfile');

    // Enter data that violates backend validation rules
    cy.get('input#age').clear().type('10'); // Age must be >= 18
    cy.get('input#weight').clear().type('1000'); // Weight must be <= 500

    // Click save
    cy.get('button[type="submit"]').contains('Salvar').click();

    // Wait for the API call and assert the response status
    cy.wait('@updateProfile').its('response.statusCode').should('eq', 422);

    // Assert that user-friendly error messages are displayed on the screen
    cy.contains('greater than or equal to 18', { timeout: 10000 }).should('be.visible');
    cy.contains('less than or equal to 500', { timeout: 10000 }).should('be.visible');
  });
});
