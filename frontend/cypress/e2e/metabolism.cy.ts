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
    
    // Intercept Login
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt-token' }
    }).as('login');
    
    // Add other mocks to prevent errors
    cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
    cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
    cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats');
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    
    // Bypass UI login to avoid timeouts
    cy.visit('/');
    cy.window().then((win) => {
        win.localStorage.setItem('jwt_token', 'fake-jwt-token');
    });
    cy.reload();

    // Wait for app to be ready and sidebar to serve
    cy.get('app-sidebar').should('be.visible');
    cy.get('[data-cy="nav-metabolism"]').should('be.visible').click();
  });

  it('should display metabolism page content', () => {
    cy.wait('@getMetabolism');
    cy.contains('Seu Metabolismo').should('be.visible');
    
    // Check main TDEE display
    cy.contains('Gasto Calórico Diário').should('be.visible');
    cy.contains('2500').should('be.visible');
    cy.contains('kcal').should('be.visible');
    
    // Check confidence
    cy.contains('Confiança').should('be.visible');
    cy.contains('high').should('be.visible'); 
    
    // Check Stats Grid
    cy.contains('Média Consumida').should('be.visible');
    cy.contains('2400').should('be.visible');
    
    cy.contains('Variação de Peso').should('be.visible');
    cy.contains('-0.5').should('be.visible');
    
    cy.contains('Dados Analisados').should('be.visible');
    cy.contains('21').should('be.visible');
    
    // Recommendation (Implicit check based on logic, mocked high confidence so recommendation shows)
    cy.contains('Sugerido:').should('be.visible');
  });

  it('should handle insufficient data state', () => {
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
    
    cy.reload();
    cy.wait('@getMetabolismEmpty');
    
    cy.contains('Sem Dados').should('be.visible');
    cy.contains('Como funciona?').should('be.visible');
  });
});
