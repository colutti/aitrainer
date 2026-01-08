describe('Trainer Settings Flow', () => {
  beforeEach(() => {
    // Intercept the API call to ensure we have data or mock it if needed
    // For now we assume the backend is running and returns data, 
    // but we can spy on it to wait for it.
    cy.intercept('GET', '**/available_trainers').as('getTrainers');
    cy.intercept('GET', '**/trainer_profile').as('getProfile');

    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    
    // Ensure navigation to settings
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button', { timeout: 10000 }).contains('Ajustes do Trainer').should('be.visible').click();
    
    // Wait for data to load
    cy.wait('@getTrainers');
  });

  it('should display the trainer selection grid', () => {
    // Check new header
    cy.contains('h2', 'Escolha seu Treinador').should('be.visible');
    cy.contains('p', 'Selecione o profissional').should('be.visible');

    // Check that we have trainer cards
    cy.get('.trainer-card').should('have.length.at.least', 1);
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
    // Find a card that is NOT currently selected
    // We assume 'atlas' is default, so let's try to click 'luna' or just the second one
    cy.get('.trainer-card').eq(1).as('targetCard');
    
    cy.get('@targetCard').click();
    
    // Verify it gets the selection styling (ring)
    cy.get('@targetCard').should('have.class', 'ring-primary');

    // Save
    cy.get('button').contains('Confirmar Escolha').click();

    // Verify success message (checking for the updated success indicator)
    cy.contains('Treinador atualizado com sucesso!', { timeout: 10000 }).should('be.visible');
  });
});

