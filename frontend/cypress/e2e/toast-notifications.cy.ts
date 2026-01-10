describe('Toast Notifications', () => {
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
                trainer_type: 'atlas'
            }
        }).as('userProfile');

        // Intercept trainer profile
        cy.intercept('GET', '**/trainer/trainer_profile', {
            statusCode: 200,
            body: {
                trainer_type: 'atlas'
            }
        }).as('trainerProfile');

        // Intercept available trainers - CORRECT STRUCTURE
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

        // Intercept Update Profile
        cy.intercept('PUT', '**/trainer/update_trainer_profile', {
            statusCode: 200,
            body: { trainer_type: 'luna' }
        }).as('updateTrainer');

        cy.login('cypress_user@test.com', 'password123');
    });

    it('should show success toast when updating trainer settings', () => {
        // 1. Navigate to Trainer Settings
        cy.get('app-sidebar button').contains('Ajustes do Trainer').click();
        cy.wait(['@trainerProfile', '@availableTrainers']);

        // 2. Click on a different trainer (Luna)
        // We use the data-testid I added in previous step (wait, did I add it? No. I need to rely on text or classes)
        // I did not add data-testid in my edit of TrainerSettingsComponent.html (I only removed success block).
        // But the file content I viewed earlier had `[attr.data-testid]="'trainer-card-' + trainer.trainer_id"`.
        // Let's verify if that was already there.
        
        // Yes, line 28 of viewed file: `[attr.data-testid]="'trainer-card-' + trainer.trainer_id"`
        cy.get('[data-testid="trainer-card-luna"]').click();

        // 3. Click Save
        cy.get('button').contains('Confirmar Escolha').click();
        cy.wait('@updateTrainer');

        // 4. Assert Toast is visible
        cy.contains('Treinador atualizado com sucesso!')
          .closest('div')
          .should('have.class', 'bg-green-900/90') // Check success style
          .should('be.visible');
    });
});
