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
    cy.intercept('GET', '**/workout/stats', { body: {} }).as('getStats'); // Mock stats as we land on dashboard first

    cy.login('cypress_user@test.com', 'password123');
    
    // Navigate to Workouts
    // Wait for dashboard or sidebar to be ready
    cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
    cy.get('[data-cy="nav-workouts"]').click();
  });

  it('should display list of workouts', () => {
    cy.wait('@getWorkouts');
    cy.get('h1').contains('Histórico').should('be.visible');
    // Use specific container checking
    cy.get('.space-y-4').contains('Pernas').should('be.visible');
    cy.get('.space-y-4').contains('Peito').should('be.visible');
  });

  it('should filter workouts', () => {
    cy.wait('@getWorkouts');
    
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
    cy.wait('@getWorkouts');
    // Click specifically on the card content check
    cy.get('.group').contains('Pernas').click();
    
    // Check Drawer
    cy.get('app-workout-drawer').should('be.visible');
    cy.get('app-workout-drawer').contains('h2', 'Pernas');
  });

  it('should close drawer', () => {
    cy.wait('@getWorkouts');
    cy.get('.group').contains('Pernas').click();
    cy.get('app-workout-drawer').should('be.visible');
    
    // Click close button
    cy.wait(500);
    cy.get('app-workout-drawer button').first().click(); 
    cy.get('app-workout-drawer').should('not.exist');
  });

  it('should check mobile viewport layout', () => {
      cy.viewport('iphone-x');
      cy.wait('@getWorkouts'); 
      
      // Test drawer interaction on mobile
      // Ensure we re-find the element in case viewport change caused re-render
      cy.get('.group').contains('Pernas').click();
      cy.get('app-workout-drawer').should('be.visible');
  });
});
