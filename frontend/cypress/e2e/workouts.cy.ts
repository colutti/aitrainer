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
    
    // Ensure loading is finished and view is stable
    cy.get('.animate-spin').should('not.exist');
    cy.wait(500); 
    
    cy.get('h1').contains('Histórico').should('be.visible');
    
    // Verify count text (this comes from the service state)
    cy.contains('2 treinos registrados').should('be.visible');

    // Verify at least one workout card exists
    cy.get('.group').should('have.length.at.least', 1);
    
    // Debug: log the number of items found
    cy.get('.group').then($els => {
        cy.log('Found ' + $els.length + ' workout cards');
    });
  });

  it('should filter workouts', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait(['@getWorkouts', '@getTypes']);
    
    // Ensure loading is finished
    cy.get('.animate-spin').should('not.exist');
    
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
    cy.get('.animate-spin').should('not.exist');

    // Click specifically on the card content check
    cy.contains('.group', 'Pernas').click({ force: true });
    
    // Wait for drawer animation to complete
    cy.wait(1000);
    
    // Check Drawer inner content visibility (avoids 0x0 host element issue)
    // We target the fixed container inside app-workout-drawer
    cy.get('app-workout-drawer').find('[role="dialog"]').should('be.visible');
    
    // Verify footer stats are present (always rendered) - this confirms drawer content is loaded
    cy.get('app-workout-drawer').contains('Volume Total').should('be.visible');
  });

  it('should close drawer', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait('@getWorkouts');
    cy.get('.animate-spin').should('not.exist');

    cy.contains('.group', 'Pernas').click({ force: true });
    
    // Use the robust selector again
    cy.get('app-workout-drawer').find('[role="dialog"]').should('be.visible');
    
    // Click close button
    cy.wait(500);
    cy.get('app-workout-drawer button').first().click(); 
    
    // Assert it is closed (not in DOM or hidden)
    cy.get('app-workout-drawer').should('not.exist');
  });

  it('should check mobile viewport layout', () => {
    cy.viewport('iphone-x');
    cy.get('[data-cy="mobile-menu-btn"]').click();
    cy.contains('button', 'Treinos').click({ force: true });
    
    cy.get('h1').contains('Histórico').should('be.visible');
    cy.wait('@getWorkouts'); 
    cy.get('.animate-spin').should('not.exist');
      
      // Test drawer interaction on mobile
      // Ensure we re-find the element in case viewport change caused re-render
      cy.get('.group').contains('Pernas').click();
      
      // Robust selector
      cy.get('app-workout-drawer').find('[role="dialog"]').should('be.visible');
  });
});
