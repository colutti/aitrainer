describe('Authorization Flow', () => {
  it('should not display the main app if the user is not logged in', () => {
    cy.visit('/', { timeout: 60000 });
    // Without logging in, the sidebar should not exist
    cy.get('app-sidebar').should('not.exist');
    // And the login component should be visible
    cy.get('app-login', { timeout: 20000 }).should('be.visible');
  });

  it('should log the user out and redirect to login on API 401 error', () => {
    // 1. Mock Login (No real API call)
    cy.mockLogin();

    // 2. Intercept the next GET request to user profile and force a 401 response
    cy.intercept('GET', '**/user/profile', {
      statusCode: 401,
      body: { detail: 'Invalid or expired token' },
    }).as('getProfile401');

    // 3. Trigger the API call by navigating to the page
    cy.get('app-sidebar button').contains('Meu Perfil').click();

    // 4. Wait for the intercepted call to happen
    cy.wait('@getProfile401');

    // 5. Assert that the user is logged out and sees the login page
    cy.get('app-login').should('be.visible');
    cy.get('app-sidebar').should('not.exist');
  });
});
