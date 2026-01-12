describe('Workout History & Drawer', () => {
  beforeEach(() => {
    // Intercept Login
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt-token' }
    }).as('login');

    cy.intercept('GET', '**/workout/list*', {
      statusCode: 200,
      body: {
        workouts: [
          {
            id: '1',
            user_email: 'cypress@test.com',
            date: '2024-01-01T10:00:00',
            workout_type: 'Pernas',
            duration_minutes: 60,
            exercises: [
              { name: 'Agachamento', sets: 3, reps_per_set: [10, 10, 10], weights_per_set: [100, 100, 100] }
            ]
          },
          {
            id: '2',
            user_email: 'cypress@test.com',
            date: '2024-01-02T10:00:00',
            workout_type: 'Peito',
            duration_minutes: 45,
            exercises: []
          }
        ],
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1
      }
    }).as('getWorkouts');

    cy.intercept('GET', '**/workout/types', ['Pernas', 'Peito', 'Costas']).as('getTypes');
    cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
    cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
    cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
    cy.intercept('GET', '**/workout/stats', { body: { streak: 0, frequency: [], last_workout: null, prs: [], volume_data: [] } }).as('getStats');
    cy.intercept('GET', '**/nutrition/stats', { body: { daily_target: 2000, current_macros: { calories: 0, protein: 0, carbs: 0, fat: 0 } } }).as('getNutritionStats');
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

  it('should display list of workouts', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait('@getWorkouts');
    cy.get('h1').contains('Histórico').should('be.visible');
    // Use specific container checking
    cy.get('.space-y-4').contains('Pernas').should('be.visible');
    cy.get('.space-y-4').contains('Peito').should('be.visible');
    
    // Verify Date Format (Portuguese)
    // Mock date: 2024-01-01 -> "01 jan 2024"
    // Intl format: dd MMM yyyy -> 01 jan. 2024 (depending on browser, pt-BR might have dot or not)
    // We check for "jan" and "2024"
    cy.contains(/01 jan\.? 2024/i).should('be.visible');
  });

  it('should filter workouts', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait(['@getWorkouts', '@getTypes']);
    
    // Open filter dropdown (assuming it exists or clicking to show search)
    
    // Mock filtered response
    cy.intercept('GET', '**/workout/list*workout_type=Pernas*', {
      statusCode: 200,
      body: {
        workouts: [
           { id: '1', workout_type: 'Pernas', date: '2024-01-01', exercises: [] }
        ],
        total: 1, page: 1, page_size: 10, total_pages: 1
      }
    }).as('getFiltered');

    cy.get('select').select('Pernas');
    cy.wait('@getFiltered');
    
    cy.get('.space-y-4').contains('Pernas').should('be.visible');
    cy.get('.space-y-4').contains('Peito').should('not.exist');
  });

  it('should open drawer on click', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait('@getWorkouts');
    // Click specifically on the card content check
    cy.contains('.group', 'Pernas').click({ force: true });
    
    // Check Drawer
    cy.get('app-workout-drawer').should('be.visible');
    cy.get('app-workout-drawer').contains('h2', 'Pernas');
    
    // Verify Date Header in Drawer
    // "01 jan 2024 • 10:00" or "01 jan. 2024"
    cy.get('app-workout-drawer').contains(/01 jan\.? 2024/i).should('be.visible');
  });

  it('should close drawer', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait('@getWorkouts');
    cy.contains('.group', 'Pernas').click({ force: true });
    cy.get('app-workout-drawer').should('be.visible');
    
    // Click close button
    cy.wait(500);
    cy.get('app-workout-drawer button').first().click(); 
    cy.get('app-workout-drawer').should('not.exist');
  });

  it('should check mobile viewport layout', () => {
    cy.viewport('iphone-x');
    cy.get('[data-cy="mobile-menu-btn"]').click();
    cy.contains('button', 'Treinos').click({ force: true });
    
    cy.get('h1').contains('Histórico').should('be.visible');
    cy.wait('@getWorkouts'); 
      
      // Test drawer interaction on mobile
      // Ensure we re-find the element in case viewport change caused re-render
      cy.get('.group').contains('Pernas').click();
      cy.get('app-workout-drawer').should('be.visible');
  });
});
