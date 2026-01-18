describe('Error Handling', () => {
  beforeEach(() => {
    // 100% Mocked Login
    cy.mockLogin();

    // Ensure we land on app
    cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
    cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
  });

    it('should display error message when chat API fails', () => {
        // Navigate to chat
        cy.contains('button', 'Chat').click({ force: true });
        cy.get('app-chat', { timeout: 10000 }).should('be.visible');

        // Intercept the message API and return an error
        cy.intercept('POST', '**/message/message', {
            statusCode: 500,
            body: { detail: 'Internal server error' },
        }).as('messageError');

        // Send a message
        cy.get('textarea[name="newMessage"]').type('Teste de erro');
        cy.get('button[type="submit"]').click();

        // Wait for the intercepted call
        cy.wait('@messageError');

        // Should display the error message from the chat service
        cy.contains('Erro ao se comunicar com o servidor.').should('be.visible');
    });

    it('should handle network timeout gracefully on chat', () => {
        // Navigate to chat
        cy.contains('button', 'Chat').click({ force: true });
        cy.get('app-chat', { timeout: 10000 }).should('be.visible');

        // Intercept with a failure
        cy.intercept('POST', '**/message/message', {
            forceNetworkError: true,
        }).as('networkError');

        // Send a message
        cy.get('textarea[name="newMessage"]').type('Teste timeout');
        cy.get('button[type="submit"]').click();

        // Should display the error message
        cy.contains('Erro ao se comunicar com o servidor.').should('be.visible');
    });

    it('should handle API error when loading user profile', () => {
        // Intercept profile API to return error
        cy.intercept('GET', '**/user/profile', {
            statusCode: 500,
            body: { detail: 'Database error' },
        }).as('profileError');

        // Navigate to user profile
        cy.contains('button', 'Meu Perfil').click({ force: true });

        // Wait for intercepted call
        cy.wait('@profileError');

        // Profile page should still be visible (just with empty/default data or showing error)
        cy.get('app-user-profile').should('be.visible');
    });

    it('should handle API error when loading trainer profile', () => {
        // Intercept trainer profile API to return error
        cy.intercept('GET', '**/trainer/trainer_profile', {
            statusCode: 500,
            body: { detail: 'Database error' },
        }).as('trainerError');

        // Navigate to trainer settings
        cy.contains('button', 'Ajustes do Trainer').click({ force: true });

        // Wait for intercepted call
        cy.wait('@trainerError');

        // Sidebar still visible
        cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
    });
});
