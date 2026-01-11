describe('Dashboard View', () => {
  beforeEach(() => {
    // Intercept Login
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: 'fake-jwt-token' }
    }).as('login');

    // Intercept stats
    cy.intercept('GET', '**/workout/stats', {
      statusCode: 200,
      body: {
        current_streak_weeks: 5,
        weekly_frequency: [true, false, true, false, true, false, false], // M, W, F
        weekly_volume: [
          { category: 'Pernas', volume: 5000 },
          { category: 'Peito', volume: 3000 },
          { category: 'Costas', volume: 4000 }
        ],
        recent_prs: [
          { exercise_name: 'Agachamento', weight: 120, reps: 5, date: new Date().toISOString(), workout_id: '1' },
          { exercise_name: 'Supino', weight: 100, reps: 8, date: new Date().toISOString(), workout_id: '2' }
        ],
        total_workouts: 42,
        last_workout: {
          id: 'last',
          user_email: 'cypress@test.com',
          date: new Date().toISOString(),
          workout_type: 'Full Body',
          duration_minutes: 75
        }
      }
    }).as('getStats');
    
    cy.intercept('GET', '**/nutrition/stats', { body: {} }).as('getNutritionStats');
    cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
    cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
    cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
    
    cy.login('cypress_user@test.com', 'password123'); // Password doesn't matter with mock
  });

  it('should land on dashboard after login', () => {
    cy.get('app-dashboard').should('be.visible');
    cy.contains('h1', 'Dashboard');
  });

  it('should display correct streak', () => {
    cy.wait('@getStats');
    cy.contains('Sequência Atual');
    cy.contains('5').should('be.visible');
    cy.contains('semanas').should('be.visible');
  });

  it('should display frequency dots', () => {
    cy.wait('@getStats');
    cy.contains('Frequência Semanal');
    // We expect 3 active days (bg-primary)
    cy.get('.bg-primary.shadow-\\[0_0_12px_rgba\\(16\\,185\\,129\\,0\\.6\\)\\]').should('have.length', 3);
  });

  it('should display last workout info', () => {
    cy.wait('@getStats');
    cy.contains('Último Treino');
    cy.contains('Full Body');
    cy.contains('75 min');
    
    // Verify Date Format (Portuguese)
    const today = new Date();
    // Expected format: "dd MMM, HH:mm" (e.g., 09 jan., 12:17 or 09 jan, 12:17 depending on browser)
    // We check for month abbreviation in Portuguese
    const month = today.toLocaleString('pt-BR', { month: 'short' }).replace('.', ''); // "jan"
    // Use regex to be flexible about dot and spacing
    cy.contains('Último Treino').parent().contains(new RegExp(month, 'i')).should('be.visible');
  });

  it('should display volume chart', () => {
    cy.wait('@getStats');
    cy.contains('Volume por Categoria');
    cy.get('canvas').should('be.visible');
  });

  it('should display recent PRs', () => {
    cy.wait('@getStats');
    cy.contains('Recordes Recentes');
    cy.contains('Agachamento');
    cy.contains('120');
    cy.contains('kg');
    cy.contains('Supino');
  });
  
  it('should navigate to chat and back to dashboard', () => {
      cy.get('button').contains('Chat').click();
      cy.get('app-chat').should('be.visible');
      cy.get('app-dashboard').should('not.exist');
      
      cy.get('button').contains('Home').click();
      cy.get('app-dashboard').should('be.visible');
  });

  it('should show loading state', () => {
      // Re-intercept with delay to force loading state visibility
      cy.intercept('GET', '**/workout/stats', {
          delay: 1000,
          statusCode: 200,
          body: {}
      }).as('getStatsDelayed');

      // Reload to trigger fetch
      cy.reload();
      
      // Check for spinner
      cy.get('.animate-spin').should('be.visible');
      
      // Wait for finish
      cy.wait('@getStatsDelayed');
      cy.get('.animate-spin').should('not.exist');
  });

  it('should check mobile viewport layout', () => {
      cy.viewport('iphone-x');
      cy.reload(); // Reload to ensure responsive classes apply if needed (usually media queries handle it, but good practice)
      cy.wait('@getStats');
      
      cy.get('app-dashboard').should('be.visible');
      // In mobile, grid columns should be 1
      // checking grid class or just visibility of widgets stacked
      // We can check if widgets are full width or stacked
      cy.get('.grid').should('have.class', 'grid-cols-1');
      
      // Check sidebar is hidden or converted to mobile menu (if implemented)
      // Assuming sidebar might be hidden on small screens or different layout
      // The current sidebar implementation is fixed width w-64, likely hidden or overlay on mobile.
      // But let's verify dashboard content visibility first.
      cy.contains('Dashboard').should('be.visible');
  });
});
