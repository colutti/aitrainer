describe('Trainer Settings Flow', () => {
  beforeEach(() => {
    // 100% Mocked Login
    cy.mockLogin({
      intercepts: {
        '**/trainer/available_trainers': {
          statusCode: 200,
          body: [
            { trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png', short_description: 'Desc', catchphrase: 'Phrase' },
            { trainer_id: 'luna', name: 'Luna', avatar_url: '/assets/luna.png', short_description: 'Desc', catchphrase: 'Phrase' }
          ],
          alias: 'getTrainers'
        },
        'PUT **/trainer/update_trainer_profile': {
          statusCode: 200,
          body: { trainer_type: 'luna' },
          alias: 'updateTrainer'
        },
        'GET **/trainer/trainer_profile': {
            statusCode: 200,
            body: { trainer_type: 'atlas' },
            alias: 'getProfile'
        }
      }
    });

    // Navigate to settings
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button', { timeout: 10000 }).contains('Ajustes do Trainer').should('be.visible').click();
    
    // Wait for data to load
    cy.wait('@getTrainers');
  });

  it('should display the trainer selection grid', () => {
    // Check header
    cy.contains('h2', 'Escolha seu Treinador').should('be.visible');

    // Check that we have trainer cards
    cy.get('.trainer-card').should('have.length', 2);
  });

  it('should display trainer details on cards', () => {
    // Check for specific elements within a card
    cy.get('.trainer-card').first().within(() => {
        cy.get('[data-testid="trainer-name"]').should('be.visible');
        cy.get('[data-testid="trainer-avatar"]').should('be.visible');
        cy.get('[data-testid="trainer-description"]').should('be.visible');
    });
  });

  it('should allow selecting a different trainer', () => {
    // Find a card that is NOT currently selected ('luna' at index 1)
    cy.get('.trainer-card').eq(1).as('targetCard');
    
    cy.get('@targetCard').click();
    
    // Verify it gets the selection styling
    cy.get('@targetCard').should('have.class', 'ring-primary');

    // Save
    cy.get('button').contains('Confirmar Escolha').click();

    // Verify success message
    cy.wait('@updateTrainer');
    cy.contains('Treinador atualizado com sucesso!', { timeout: 10000 }).should('be.visible');
  });
});

