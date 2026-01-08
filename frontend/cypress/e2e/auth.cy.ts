describe('Authorization Flow', () => {
  it('should not display the main app if the user is not logged in', () => {
    cy.visit('/');
    // Without logging in, the sidebar should not exist
    cy.get('app-sidebar').should('not.exist');
    // And the login component should be visible
    cy.get('app-login').should('be.visible');
  });

  // More tests will be added here
  it('should log the user out and redirect to login on API 401 error', () => {
    // 1. Login normally
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');

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
