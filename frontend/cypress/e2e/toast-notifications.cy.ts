describe('Toast Notifications', () => {
    beforeEach(() => {
        // Essential startup intercepts for Dashboard
        cy.intercept('GET', '**/trainer/trainer_profile', {
            statusCode: 200,
            body: { trainer_type: 'atlas' }
        }).as('trainerProfile');
        
        cy.intercept('GET', '**/trainer/available_trainers', {
            statusCode: 200,
            body: [
                { 
                    trainer_id: 'atlas', 
                    name: 'Atlas', 
                    gender: 'Masculino',
                    avatar_url: '/assets/atlas.png',
                    short_description: 'Desc',
                    catchphrase: 'Phrase',
                    specialties: ['Force']
                },
                { 
                    trainer_id: 'luna', 
                    name: 'Luna',
                    gender: 'Feminino',
                    avatar_url: '/assets/luna.png',
                    short_description: 'Desc',
                    catchphrase: 'Phrase',
                    specialties: ['Yoga']
                }
            ]
        }).as('availableTrainers');

        cy.intercept('GET', '**/message/history*', { body: [] }).as('chatHistory');
        cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
        cy.intercept('GET', '**/workout/stats', { body: { streak: 0, frequency: [] } }).as('getWorkoutStats');
        cy.intercept('GET', '**/nutrition/stats', { body: { daily_target: 2000, current_macros: {} } }).as('getNutritionStats');
        cy.intercept('GET', '**/user/profile', { body: { email: 'cypress@test.com' } }).as('userProfile');

        // Intercept Update Profile
        cy.intercept('PUT', '**/trainer/update_trainer_profile', {
            statusCode: 200,
            body: { trainer_type: 'luna' }
        }).as('updateTrainer');

        // Bypass UI login
        cy.visit('/', {
            onBeforeLoad: (win) => {
                win.localStorage.setItem('jwt_token', 'fake-jwt-token');
            }
        });

        // Ensure we land on app
        cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
    });

    it('should show success toast when updating trainer settings', () => {
        // 1. Navigate to Trainer Settings
        cy.contains('button', 'Ajustes do Trainer').click({ force: true });
        cy.wait(['@trainerProfile', '@availableTrainers']);

        // 2. Click on a different trainer (Luna)
        cy.get('[data-testid="trainer-card-luna"]').click();

        // 3. Click Save
        cy.get('button').contains('Confirmar Escolha').click();
        cy.wait('@updateTrainer');

        // 4. Assert Toast is visible
        cy.contains('Treinador atualizado com sucesso!', { timeout: 10000 })
          .should('be.visible');
    });
});
