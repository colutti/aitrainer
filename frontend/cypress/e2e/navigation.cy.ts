describe('Navigation Flow', () => {
    beforeEach(() => {
        // Intercept Login
        cy.intercept('POST', '**/user/login', {
            statusCode: 200,
            body: { token: 'fake-jwt-token' }
        }).as('login');

        // Intercept stats (dashboard)
        cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats');

        // Intercept chat history
        cy.intercept('GET', '**/message/history*', {
            statusCode: 200,
            body: { messages: [] }
        }).as('chatHistory');

        // Intercept user profile
        cy.intercept('GET', '**/user/profile', {
            statusCode: 200,
            body: {
                email: 'cypress@test.com',
                gender: 'Masculino',
                age: 30,
                weight: 80,
                height: 180,
                goal: 'Ganhar massa'
            }
        }).as('userProfile');

        // Intercept trainer profile
        cy.intercept('GET', '**/trainer/trainer_profile', {
            statusCode: 200,
            body: {
                user_email: 'cypress@test.com',
                trainer_type: 'sofia',
                personality_traits: ['motivador', 'técnico']
            }
        }).as('trainerProfile');

        // Intercept available trainers list
        cy.intercept('GET', '**/trainer/available_trainers', {
            statusCode: 200,
            body: [
                { id: 'sofia', name: 'Sofia', description: 'Motivadora e empática' },
                { id: 'atlas', name: 'Atlas', description: 'Técnico e focado' },
                { id: 'luna', name: 'Luna', description: 'Calma e mindful' },
                { id: 'sargento', name: 'Sargento', description: 'Disciplinado e direto' }
            ]
        }).as('availableTrainers');

        cy.login('cypress_user@test.com', 'password123');
    });

    it('should navigate from Dashboard to User Profile', () => {
        // Start on dashboard (default after login)
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');

        // Navigate to user profile
        cy.get('app-sidebar button').contains('Meu Perfil').click();
        cy.wait('@userProfile');

        // Verify correct view is displayed
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');
        cy.get('app-dashboard').should('not.exist');
    });

    it('should navigate from User Profile to Trainer Settings', () => {
        // Go to user profile first
        cy.get('app-sidebar button').contains('Meu Perfil').click();
        cy.wait('@userProfile');
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');

        // Navigate to trainer settings
        cy.get('app-sidebar button').contains('Ajustes do Trainer').click();
        cy.wait('@trainerProfile');

        // Verify correct view is displayed
        cy.get('app-trainer-settings', { timeout: 10000 }).should('be.visible');
        cy.get('app-user-profile').should('not.exist');
    });

    it('should navigate from Trainer Settings back to Dashboard', () => {
        // Go to trainer settings first
        cy.get('app-sidebar button').contains('Ajustes do Trainer').click();
        cy.wait('@trainerProfile');
        cy.get('app-trainer-settings', { timeout: 10000 }).should('be.visible');

        // Navigate back to dashboard
        cy.get('app-sidebar button').contains('Home').click();

        // Verify correct view is displayed
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
        cy.get('app-trainer-settings').should('not.exist');
    });

    it('should highlight the active navigation button', () => {
        // Wait for dashboard to load
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
        
        // Home button should be active initially
        cy.get('app-sidebar button').contains('Home')
            .closest('button')
            .should('have.class', 'bg-primary');

        // Navigate to user profile
        cy.get('app-sidebar button').contains('Meu Perfil').click();
        cy.wait('@userProfile');
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');

        // User profile button should now be active
        cy.get('app-sidebar button').contains('Meu Perfil')
            .closest('button')
            .should('have.class', 'bg-primary');

        // Home button should no longer be active
        cy.get('app-sidebar button').contains('Home')
            .closest('button')
            .should('not.have.class', 'bg-primary');
    });
});
