describe('Workout History & Drawer', () => {
  const mockWorkouts = {
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
  };

  beforeEach(() => {
    // 100% Mocked Login with custom intercepts and aliases
    cy.mockLogin({
      intercepts: {
        '**/workout/list*': { statusCode: 200, body: mockWorkouts, alias: 'getWorkouts' },
        '**/workout/types': { body: ['Pernas', 'Peito', 'Costas'], alias: 'getTypes' }
      }
    });
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

  it('should delete a workout', () => {
    cy.get('[data-cy="nav-workouts"]').click({ force: true });
    cy.wait('@getWorkouts');
    cy.get('.animate-spin').should('not.exist');

    // Intercept DELETE
    cy.intercept('DELETE', '**/workout/1', {
      statusCode: 200,
      body: { message: 'Workout deleted successfully' }
    }).as('deleteWorkout');

    // Mock re-fetch after deletion (only 1 workout left)
    cy.intercept('GET', '**/workout/list*', {
      statusCode: 200,
      body: {
        workouts: [mockWorkouts.workouts[1]],
        total: 1, page: 1, page_size: 10, total_pages: 1
      }
    }).as('getWorkoutsAfterDelete');

    // Trigger delete on the first card
    // Use data-cy for reliable selection
    cy.get('[data-cy="delete-workout"]').first().click({ force: true });

    // Confirm browser dialog
    cy.on('window:confirm', () => true);

    cy.wait('@deleteWorkout');
    cy.wait('@getWorkoutsAfterDelete');

    // Verify it was removed from UI (specifically in the list)
    cy.get('.space-y-4').contains('Pernas').should('not.exist');
    cy.get('.space-y-4').contains('Peito').should('be.visible');
    cy.contains('1 treinos registrados').should('be.visible');
  });
});
