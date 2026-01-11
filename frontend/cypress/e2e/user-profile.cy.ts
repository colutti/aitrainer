describe('User Profile Flow', () => {
  beforeEach(() => {
    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats');
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    cy.get('app-sidebar').should('be.visible');
    cy.get('app-sidebar button').contains('Meu Perfil').should('be.visible').click();
  });

  it('should display the user profile page', () => {
    cy.get('app-user-profile').should('be.visible');
    cy.contains('h2', 'Meu Perfil').should('be.visible');
  });

  it('should load existing user profile data', () => {
    // Check if some fields are pre-filled. We assume the backend has some data.
    // Let's check if the age field has a value greater than 0
    cy.get('input[name="age"]').invoke('val').should('not.be.empty');
  });

  it('should display all form fields', () => {
    // Verify all fields are present
    cy.get('input[name="age"]').should('be.visible');
    cy.get('select[name="gender"]').should('be.visible');
    cy.get('input[name="weight"]').should('be.visible');
    cy.get('input[name="height"]').should('be.visible');
    cy.get('input[name="goal"]').should('be.visible');
  });

  it('should allow updating all user profile fields', () => {
    const testData = {
      age: '30',
      weight: '75',
      height: '175',
      goal: 'Ganhar massa muscular',
    };

    // Fill all fields
    cy.get('input[name="age"]').clear().type(testData.age);
    cy.get('input[name="weight"]').clear().type(testData.weight);
    cy.get('input[name="height"]').clear().type(testData.height);
    cy.get('input[name="goal"]').clear().type(testData.goal);
    
    // Select Goal Type
    cy.get('select[name="goal_type"]').select('Perder Peso');
    cy.get('input[name="weekly_rate"]').clear().type('0.5');
    
    cy.get('select[name="gender"]').select('Masculino');

    // Save
    cy.get('button').contains('Salvar').click();

    // Check for success message
    cy.contains('Perfil salvo com sucesso!').should('be.visible');

    // Re-verify the fields have the new values after navigation
    cy.get('app-sidebar button').contains('Chat').click();
    cy.get('app-sidebar button').contains('Meu Perfil').click();

    cy.get('input[name="age"]').should('have.value', testData.age);
    cy.get('input[name="weight"]').should('have.value', testData.weight);
    cy.get('input[name="height"]').should('have.value', testData.height);
    cy.get('input[name="goal"]').should('have.value', testData.goal);
    cy.get('select[name="goal_type"]').should('have.value', 'lose'); // assuming 'Perder Peso' maps to 'lose'
    cy.get('input[name="weekly_rate"]').should('have.value', '0.5');
    cy.get('select[name="gender"]').should('have.value', 'Masculino');
  });
});

