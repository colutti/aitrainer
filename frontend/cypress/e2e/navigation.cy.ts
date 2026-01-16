describe('Navigation Flow', () => {
    let userToken: string;
    
    before(() => {
        cy.request('POST', '/api/user/login', {
          email: 'cypress_user@test.com',
          password: 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661'
        }).then((response) => {
          userToken = response.body.token;
        });
    });

    beforeEach(() => {
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

        // Essential startup intercepts for Dashboard
        cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'sofia' } }).as('trainerProfile');
        cy.intercept('GET', '**/trainer/available_trainers', { body: [{ id: 'sofia', name: 'Sofia' }] }).as('availableTrainers');
        cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
        cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
        cy.intercept('GET', '**/workout/stats', { body: { streak: 0, frequency: [] } }).as('getWorkoutStats');
        cy.intercept('GET', '**/nutrition/stats', { body: { daily_target: 2000, current_macros: {} } }).as('getNutritionStats');

        // Visit with real token from API login
        cy.visit('/', {
            onBeforeLoad: (win) => {
                win.localStorage.setItem('jwt_token', userToken);
            }
        });

        // Ensure we land on app and it's stable
        cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
    });

    it('should navigate from Dashboard to User Profile', () => {
        // Start on dashboard (default after login)
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');

        // Navigate to user profile
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');

        // Verify correct view is displayed
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');
        cy.get('app-dashboard').should('not.exist');
    });

    it('should navigate from User Profile to Trainer Settings', () => {
        // Go to user profile first
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');

        // Navigate to trainer settings
        cy.contains('button', 'Ajustes do Trainer').click({ force: true });
        cy.wait('@trainerProfile');

        // Verify correct view is displayed
        cy.get('app-trainer-settings', { timeout: 10000 }).should('be.visible');
        cy.get('app-user-profile').should('not.exist');
    });

    it('should navigate from Trainer Settings back to Dashboard', () => {
        // Go to trainer settings first
        cy.contains('button', 'Ajustes do Trainer').click({ force: true });
        cy.wait('@trainerProfile');
        cy.get('app-trainer-settings', { timeout: 10000 }).should('be.visible');

        // Navigate back to dashboard
        cy.contains('button', 'Home').click({ force: true });

        // Verify correct view is displayed
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
        cy.get('app-trainer-settings').should('not.exist');
    });

    it('should highlight the active navigation button', () => {
        // Wait for dashboard to load
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
        
        // Home button should be active initially
        cy.contains('button', 'Home')
            .should('have.class', 'bg-primary');

        // Navigate to user profile
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');

        // User profile button should now be active
        cy.contains('button', 'Meu Perfil')
            .should('have.class', 'bg-primary');

        // Home button should no longer be active
        cy.contains('button', 'Home')
            .should('not.have.class', 'bg-primary');
    });
});
