describe('Dashboard View', () => {
  beforeEach(() => {
    // Create a valid JWT structure for mocking
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const payload = btoa(JSON.stringify({ 
      email: 'cypress_user@test.com', 
      exp: Math.floor(Date.now() / 1000) + 3600 
    }));
    const signature = btoa('fake-signature');
    const fakeJWT = `${header}.${payload}.${signature}`;
    
    // Intercept Login with properly structured JWT
    cy.intercept('POST', '**/user/login', {
      statusCode: 200,
      body: { token: fakeJWT }
    }).as('login');
    
    // Intercept logout to prevent 401 errors
    cy.intercept('POST', '**/user/logout', {
      statusCode: 200,
      body: { message: 'Logged out' }
    }).as('logout');
    
    // Intercept metabolism summary to prevent 401 errors
    cy.intercept('GET', '**/metabolism/summary*', {
      statusCode: 200,
      body: { tdee: null, trend: 'maintenance' }
    }).as('getMetabolismSummary');

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
    
    // Default intercept for weight stats (can be overridden in specific tests)
    cy.intercept('GET', '**/weight/stats*', { 
      body: { latest: null, weight_trend: [], fat_trend: [], muscle_trend: [] } 
    }).as('getWeightStats');
    
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661'); // Password doesn't matter with mock
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

  it('should display body composition widget', () => {
      // Widget should be visible (will show empty state with default mock)
      cy.get('[data-cy="body-composition-widget"]').scrollIntoView().should('be.visible');
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
    cy.contains('Volume por Categoria').scrollIntoView();
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

  it('should display section headers', () => {
    cy.wait('@getStats');
    cy.contains('Corpo').scrollIntoView().should('be.visible');
    cy.contains('Treinos').scrollIntoView().should('be.visible');
    cy.contains('Nutrição').scrollIntoView().should('be.visible');
  });

  it('should allow logging weight and composition via widget', () => {
    cy.intercept('POST', '**/weight', { statusCode: 200, body: { message: 'Weight logged' } }).as('logWeight');
    
    // Check widget presence
    cy.contains('Log de Composição').should('be.visible');
    
    // Type weight
    // First input is weight
    cy.get('app-weight-widget input').eq(0).clear().type('75.5');
    
    // Toggle expand
    cy.contains('button', 'Mais').click();
    
    // Type composition (Fat%)
    // Second input is fat
    cy.get('app-weight-widget input').eq(1).type('15.5');

    // Click save
    // Button with OK text or saving state
    cy.get('app-weight-widget button').contains('OK').click();
    
    // Verify request
    cy.wait('@logWeight').its('request.body').should('deep.include', {
        weight_kg: 75.5,
        body_fat_pct: 15.5
    });
    
    // Verify success feedback
    cy.contains('atualizada', { timeout: 10000 }).should('be.visible');
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
