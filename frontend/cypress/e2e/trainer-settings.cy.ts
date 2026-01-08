describe('Trainer Settings Flow', () => {
  beforeEach(() => {
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button', { timeout: 10000 }).contains('Ajustes do Trainer').should('be.visible').click();
  });

  it('should display the trainer settings page', () => {
    cy.get('app-trainer-settings').should('be.visible');
    cy.contains('h2', 'Ajustes do Trainer').should('be.visible');
  });

  it('should display all form fields', () => {
    // Verify all fields are present
    cy.get('input[name="name"]').should('be.visible');
    cy.get('select[name="gender"]').should('be.visible');

    cy.get('select[name="style"]').should('be.visible');
  });

  it('should allow updating all trainer settings', () => {
    const newName = 'Coach Elite';

    // Update all fields
    cy.get('input[name="name"]').clear().type(newName);
    cy.get('select[name="gender"]').select('Feminino');

    cy.get('select[name="style"]').select('Holístico');

    cy.get('button').contains('Salvar').click();

    // Check for success message
    cy.contains('Ajustes salvos com sucesso!').should('be.visible');

    // Re-verify the fields have the new values after navigation
    cy.get('app-sidebar button').contains('Chat').click();
    cy.get('app-sidebar button').contains('Ajustes do Trainer').click();

    cy.get('input[name="name"]').should('have.value', newName);
    cy.get('select[name="gender"]').should('have.value', 'Feminino');

    cy.get('select[name="style"]').should('have.value', 'Holístico');
  });
});

