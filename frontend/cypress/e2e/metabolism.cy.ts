describe('Metabolism Page', () => {
  beforeEach(() => {
    // Intercepts
    cy.intercept('GET', '**/metabolism/summary*', {
        statusCode: 200,
        body: {
            tdee: 2500,
            confidence: 'high',
            avg_calories: 2400,
            weight_change_per_week: -0.5,
            logs_count: 21,
            startDate: new Date().toISOString(),
            endDate: new Date().toISOString(),
            start_weight: 80.0,
            end_weight: 78.5
        }
    }).as('getMetabolism');
    
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt-token' }
    }).as('login');

    // Essential startup intercepts for Dashboard
    cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
    cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
    cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats');
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
    
    // Bypass UI login using onBeforeLoad
    cy.visit('/', {
        onBeforeLoad: (win) => {
            win.localStorage.setItem('jwt_token', 'fake-jwt-token');
        }
    });

    // Wait for app to be ready
    cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
  });

  it('should display metabolism page content', () => {
    cy.contains('button', 'Metabolismo').click({ force: true });
    cy.wait('@getMetabolism');
    cy.get('app-metabolism').should('be.visible');
    cy.contains('Seu Metabolismo').should('be.visible');
    
    // Check main TDEE display
    cy.contains('Sua Meta Diária (Comer)').should('be.visible');
    cy.contains('2500').should('be.visible');
    
    // Check confidence
    // cy.contains('Confiança').should('be.visible');
    // cy.contains('high').should('be.visible'); 
    
    // Check Stats Grid with flexible number matching
    cy.contains('Ingestão Média').scrollIntoView().should('be.visible');
    cy.contains('2400').should('be.visible');
    
    cy.contains('Tendência de Peso').scrollIntoView().should('be.visible');
    cy.contains('80').should('be.visible');
    cy.contains('78').should('be.visible');
    
    cy.contains('Período Analisado').scrollIntoView().should('be.visible');
    cy.contains('21').should('be.visible');
    
    // Recommendation (Implicit check based on logic, mocked high confidence so recommendation shows)
    // cy.contains('Sua meta diária recomendada é de').should('be.visible');
  });

  it('should handle insufficient data state', () => {
      // Define the specific intercept for this test
      cy.intercept('GET', '**/metabolism/summary*', {
        statusCode: 200,
        body: {
            tdee: 0,
            confidence: 'none',
            avg_calories: 0,
            weight_change_per_week: 0,
            logs_count: 5,
            startDate: '',
            endDate: '',
            start_weight: 0,
            end_weight: 0,
            message: 'Insufficient data'
        }
    }).as('getMetabolismEmpty');
    
    // Navigate elsewhere and back to trigger request
    cy.contains('button', 'Home').click({ force: true });
    cy.contains('button', 'Metabolismo').click({ force: true });
    
    cy.wait('@getMetabolismEmpty');
    
    cy.contains('Sem Dados').scrollIntoView().should('be.visible');
    cy.contains('Como funciona a calibração?').scrollIntoView().should('be.visible');
  });
});
