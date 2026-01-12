describe('Body Composition Page', () => {
  beforeEach(() => {
    // Intercept Login
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt-token' }
    }).as('login');

    // Intercept unrelated calls that might trigger on Dashboard load
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getWorkoutStats');
    cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
    
    // Essential startup intercepts
    cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
    cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
    cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
    
    // Login before each test
    cy.login('demo@demo.com', 'password');
    // Ensure we are on dashboard initially
    cy.visit('/');
  });

  it('navigates to body composition page via sidebar', () => {
    // Click sidebar link text instead of data attribute to be safe
    cy.contains('button', 'Composição').click({ force: true });
    
    cy.contains('h1', 'Composição Corporal').should('be.visible');
  });

  it('displays hero card content when data exists', () => {
     // Mocking data could be done here if we wanted reliable test independent of DB state.
     // For now, assuming demo data or we let it fail if empty (which prompts us to run import).
     // Ideally we intercept the API call.
     
     cy.intercept('GET', '**/weight/stats', {
         statusCode: 200,
         body: {
             latest: {
                 user_email: 'demo@demo.com',
                 date: '2026-01-01',
                 weight_kg: 80.5,
                 body_fat_pct: 20.5,
                 muscle_mass_pct: 50.0,
                 bmr: 1800
             },
             weight_trend: [],
             fat_trend: [],
             muscle_trend: []
         }
     }).as('getStats');
     
     cy.intercept('GET', '**/weight?limit=30', { body: [] }).as('getHistoryMock');

     cy.contains('button', 'Composição').click({ force: true });
     cy.wait(['@getStats', '@getHistoryMock']);

     cy.get('[data-cy="latest-weight"]').should('contain', '80.5');
     cy.get('[data-cy="latest-body-fat"]').should('contain', '20,50');
  });

  it('displays history table', () => {
       cy.contains('button', 'Composição').click({ force: true });
       cy.get('[data-cy="composition-history"]').should('be.visible');
  });

  it('allows manual entry of body composition data', () => {
    cy.intercept('POST', '**/weight', { statusCode: 200, body: { message: 'Success' } }).as('saveWeight');
    // Mock refresh calls
    cy.intercept('GET', '**/weight/stats', { body: { latest: null } }).as('refreshStats'); 
    cy.intercept('GET', '**/weight?limit=30', { body: [] }).as('refreshHistory');

    cy.contains('button', 'Composição').click({ force: true });
    
    // Fill form
    // Specific selectors based on labels would be better, but assuming order or using sibling finding
    cy.contains('label', 'Peso (kg)*').parent().find('input').type('85.5');
    cy.contains('label', 'Gordura (%)').parent().find('input').type('22.5');
    cy.contains('label', 'Músculo (%)').parent().find('input').type('40.5');
    
    cy.contains('button', 'Salvar Registro').click();
    
    cy.wait('@saveWeight').then((interception) => {
        expect(interception.request.body).to.include({
            weight_kg: 85.5,
            body_fat_pct: 22.5,
            muscle_mass_pct: 40.5
        });
    });
    
    cy.contains('Registro salvo com sucesso!').should('be.visible');
  });
});
