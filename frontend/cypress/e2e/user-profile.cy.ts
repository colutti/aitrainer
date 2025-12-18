describe('User Profile Flow', () => {
  beforeEach(() => {
    cy.login('admin', '123');
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button').contains('Meu Perfil').should('be.visible').click();
  });

  it('should display the user profile page', () => {
    cy.get('app-user-profile').should('be.visible');
    cy.contains('h2', 'Meu Perfil').should('be.visible');
  });

  it('should load existing user profile data', () => {
    // Check if some fields are pre-filled. We assume the backend has some data.
    // Let's check if the age field has a value greater than 0
    cy.get('input[name="age"]').invoke('val').should('not.be.empty');
  });

  it('should allow updating the user profile', () => {
    const newAge = '35';
    const newWeight = '80';

    cy.get('input[name="age"]').clear().type(newAge);
    cy.get('input[name="weight"]').clear().type(newWeight);
    cy.get('button').contains('Salvar').click();

    // Check for success message
    cy.contains('Perfil salvo com sucesso!').should('be.visible');

    // Re-verify the fields have the new values after a "refresh"
    cy.get('app-sidebar button').contains('Chat').click();
    cy.get('app-sidebar button').contains('Meu Perfil').click();

    cy.get('input[name="age"]').should('have.value', newAge);
    cy.get('input[name="weight"]').should('have.value', newWeight);
  });
});
