Toast-notifications|describe('Toast Notifications', () => {
    beforeEach(() => {
        // 100% Mocked Login
        cy.mockLogin({
            intercepts: {
                '**/trainer/available_trainers': {
                    statusCode: 200,
                    body: [
                        { trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png' },
                        { trainer_id: 'luna', name: 'Luna', avatar_url: '/assets/luna.png' }
                    ],
                    alias: 'availableTrainers'
                },
                'PUT **/trainer/update_trainer_profile': {
                    statusCode: 200,
                    body: { trainer_type: 'luna' },
                    alias: 'updateTrainer'
                },
                // Explicitly adding trainer profile alias since we wait for it
                '**/trainer/trainer_profile': {
                    body: { trainer_type: 'atlas' },
                    alias: 'trainerProfile'
                }
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
