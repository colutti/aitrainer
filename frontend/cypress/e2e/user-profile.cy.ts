describe('User Profile Flow', () => {
  beforeEach(() => {
    // 100% Mocked Login
    cy.mockLogin({
      intercepts: {
        'PUT **/user/profile': {
          statusCode: 200,
          body: { message: 'Perfil salvo com sucesso!' },
          alias: 'saveProfile'
        }
      }
    });

    cy.get('app-sidebar button').contains('Meu Perfil').should('be.visible').click();
  });

  it('should display the user profile page', () => {
    cy.get('app-user-profile').should('be.visible');
    cy.contains('h2', 'Meu Perfil').should('be.visible');
  });

  it('should load existing user profile data', () => {
    // Check if some fields are pre-filled. Default comes from COMMON_MOCKS.userProfile
    cy.get('input[name="age"]').invoke('val').should('not.be.empty');
    cy.get('input[name="age"]').should('have.value', '30');
  });

  it('should display all form fields', () => {
    // Verify all fields are present
    cy.get('input[name="age"]').should('be.visible');
    cy.get('select[name="gender"]').should('be.visible');
    cy.get('input[name="weight"]').should('be.visible');
    cy.get('input[name="height"]').should('be.visible');
    cy.get('textarea[name="notes"]').should('be.visible');
  });

});

