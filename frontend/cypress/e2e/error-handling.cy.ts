describe('Error Handling', () => {
    beforeEach(() => {
        cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    });

    it('should display error message when chat API fails', () => {
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
        // Intercept with a delayed failure
        cy.intercept('POST', '**/message/message', {
            forceNetworkError: true,
        }).as('networkError');

        // Send a message
        cy.get('textarea[name="newMessage"]').type('Teste timeout');
        cy.get('button[type="submit"]').click();

        // Should display the error message
        cy.contains('Erro ao se comunicar com o servidor.', { timeout: 15000 }).should('be.visible');
    });

    it('should handle API error when loading user profile', () => {
        // Intercept profile API to return error
        cy.intercept('GET', '**/user/profile', {
            statusCode: 500,
            body: { detail: 'Database error' },
        }).as('profileError');

        // Navigate to user profile
        cy.get('app-sidebar button').contains('Meu Perfil').click();

        // Wait for intercepted call
        cy.wait('@profileError');

        // Profile page should still be visible (just with empty/default data)
        cy.get('app-user-profile').should('be.visible');
    });

    it('should handle API error when loading trainer profile', () => {
        // Intercept trainer profile API to return error
        cy.intercept('GET', '**/trainer/trainer_profile', {
            statusCode: 500,
            body: { detail: 'Database error' },
        }).as('trainerError');

        // Navigate to trainer settings
        cy.get('app-sidebar button').contains('Ajustes do Trainer').click();

        // Wait for intercepted call
        cy.wait('@trainerError');

        // Trainer settings page should still be visible with default data
        cy.get('app-trainer-settings').should('be.visible');
    });
});
