describe('Dashboard View', () => {
  beforeEach(() => {
    // Shared stats mock
    const workoutStats = {
      current_streak_weeks: 5,
      weekly_frequency: [true, false, true, false, true, false, false],
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
    };

    // 100% Mocked Login with customized intercepts and aliases
    cy.mockLogin({
      intercepts: {
        '**/workout/stats': { statusCode: 200, body: workoutStats, alias: 'getStats' },
        '**/metabolism/summary*': { statusCode: 200, body: { tdee: null, trend: 'maintenance' }, alias: 'getMetabolism' },
        '**/user/logout': { statusCode: 200, body: { message: 'Logged out' } }
      }
    });
  });

  it('should land on dashboard after login', () => {
    cy.get('app-dashboard').should('be.visible');
    cy.contains('h1', 'Dashboard');
  });

  it('should display correct streak', () => {
    cy.wait('@getStats');
    cy.contains('Sequência Atual');
    cy.contains('5').should('exist');
    cy.contains('semanas').should('exist');
  });

  it('should display frequency dots', () => {
    cy.wait('@getStats');
    cy.contains('Frequência Semanal');
    // We expect 3 active days (bg-primary)
    cy.get('.bg-primary.shadow-\\[0_0_12px_rgba\\(16\\,185\\,129\\,0\\.6\\)\\]').should('have.length', 3);
  });

  it('should display body composition widget', () => {
      // Widget should exist (will show empty state with default mock)
      // Using text content since data-cy attributes are being stripped in production build
      cy.contains('Evolução Composição').should('exist');
  });


  it('should display last workout info', () => {
    cy.wait('@getStats');
    cy.contains('Último Treino').should('exist');
    cy.contains('Full Body').should('exist');
    cy.contains('75 min').should('exist');
    
    // Verify Date Format (Portuguese)
    const today = new Date();
    // Expected format: "dd MMM, HH:mm" (e.g., 09 jan., 12:17 or 09 jan, 12:17 depending on browser)
    // We check for month abbreviation in Portuguese
    const month = today.toLocaleString('pt-BR', { month: 'short' }).replace('.', ''); // "jan"
    // Use regex to be flexible about dot and spacing
    cy.contains('Último Treino').parent().contains(new RegExp(month, 'i')).should('exist');
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
      cy.get('app-sidebar').contains('Chat').click();
      cy.get('app-chat').should('be.visible');
      cy.get('app-dashboard').should('not.exist');
      
      cy.get('app-sidebar').contains('Home').click();
      cy.get('app-dashboard').should('be.visible');
  });

  it('should show loading state', () => {
      // Re-intercept with delay to force loading state visibility
      cy.intercept('GET', '**/workout/stats', {
          delay: 3000,
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
