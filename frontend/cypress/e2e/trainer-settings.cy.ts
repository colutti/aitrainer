describe('Trainer Settings Flow', () => {
  beforeEach(() => {
    cy.login('admin', '123');
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button', { timeout: 10000 }).contains('Ajustes do Trainer').should('be.visible').click();
  });

  it('should display the trainer settings page', () => {
    cy.get('app-trainer-settings').should('be.visible');
    cy.contains('h2', 'Ajustes do Trainer').should('be.visible');
  });

  it('should allow updating the trainer settings', () => {
    cy.get('app-trainer-settings').should('be.visible');
    const newName = 'Sargento Rock';

    cy.get('select[name="humour"]').select('Rígido');
    cy.get('input[name="name"]').clear().type(newName);
    cy.get('button').contains('Salvar').click();

    // Check for success message
    cy.contains('Ajustes salvos com sucesso!').should('be.visible');

    // Re-verify the fields have the new values after a "refresh"
    cy.get('app-sidebar button').contains('Chat').click();
    cy.get('app-sidebar button').contains('Ajustes do Trainer').click();

    cy.get('select[name="humour"]').should('have.value', 'Rígido');
    cy.get('input[name="name"]').should('have.value', newName);
  });
});
