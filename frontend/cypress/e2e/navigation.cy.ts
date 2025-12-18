describe('Navigation Flow', () => {
    beforeEach(() => {
        cy.login('admin', '123');
    });

    it('should navigate from Chat to User Profile', () => {
        // Start on chat
        cy.get('app-chat').should('be.visible');

        // Navigate to user profile
        cy.get('app-sidebar button').contains('Meu Perfil').click();

        // Verify correct view is displayed
        cy.get('app-user-profile').should('be.visible');
        cy.get('app-chat').should('not.exist');
    });

    it('should navigate from User Profile to Trainer Settings', () => {
        // Go to user profile first
        cy.get('app-sidebar button').contains('Meu Perfil').click();
        cy.get('app-user-profile').should('be.visible');

        // Navigate to trainer settings
        cy.get('app-sidebar button').contains('Ajustes do Trainer').click();

        // Verify correct view is displayed
        cy.get('app-trainer-settings').should('be.visible');
        cy.get('app-user-profile').should('not.exist');
    });

    it('should navigate from Trainer Settings back to Chat', () => {
        // Go to trainer settings first
        cy.get('app-sidebar button').contains('Ajustes do Trainer').click();
        cy.get('app-trainer-settings').should('be.visible');

        // Navigate back to chat
        cy.get('app-sidebar button').contains('Chat').click();

        // Verify correct view is displayed
        cy.get('app-chat').should('be.visible');
        cy.get('app-trainer-settings').should('not.exist');
    });

    it('should highlight the active navigation button', () => {
        // Chat button should be active initially (bg-primary is on the button, not the span)
        cy.get('app-sidebar button').contains('Chat')
            .closest('button')
            .should('have.class', 'bg-primary');

        // Navigate to user profile
        cy.get('app-sidebar button').contains('Meu Perfil').click();

        // User profile button should now be active
        cy.get('app-sidebar button').contains('Meu Perfil')
            .closest('button')
            .should('have.class', 'bg-primary');

        // Chat button should no longer be active
        cy.get('app-sidebar button').contains('Chat')
            .closest('button')
            .should('not.have.class', 'bg-primary');
    });
});
