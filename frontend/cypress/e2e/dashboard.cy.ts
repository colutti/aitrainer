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
        '**/metabolism/summary*': { 
            statusCode: 200, 
            body: { 
                tdee: 2500, 
                confidence: 'medium', 
                trend: 'maintenance',
                status: 'maintenance',
                energy_balance: 100,
                start_weight: 80,
                end_weight: 79.5,
                weight_trend: [{ date: '2026-01-01', weight: 80 }, { date: '2026-01-02', weight: 79.8 }],
                consistency: [{ date: '2026-01-01', weight: true, nutrition: true }],
                fat_change_kg: -0.5,
                muscle_change_kg: 0.2,
                weight_logs_count: 10,
                startDate: '2026-01-01',
                endDate: '2026-01-10'
            }, 
            alias: 'getMetabolism' 
        },
        '**/trainer/available_trainers': { statusCode: 200, body: [{ trainer_id: 'atlas', name: 'Atlas', avatar_url: 'assets/atlas.png' }] },
        '**/trainer/trainer_profile': { statusCode: 200, body: { trainer_type: 'atlas' } },
        '**/metabolism/insight*': { statusCode: 200, body: "Analysis mock" },
        '**/nutrition/stats': { statusCode: 200, body: { today: { calories: 2000, protein_grams: 150, carbs_grams: 200, fat_grams: 60 }, last_14_days: [] } },
        '**/user/logout': { statusCode: 200, body: { message: 'Logged out' } }
      }
    });
  });

  it('should land on dashboard after login', () => {
    cy.get('app-dashboard').should('be.visible');
    cy.contains('h1', 'Dashboard');
  });

  it.skip('should display correct streak', () => {
    cy.wait('@getStats');
    cy.contains('Sequência Atual').should('exist');
  });

  it.skip('should display frequency dots', () => {
    cy.wait('@getStats');
    cy.contains('Frequência Semanal');
    cy.get('.bg-primary').should('have.length.at.least', 3);
  });

  it.skip('should display body composition widget with period and recomposition badge', () => {
      cy.intercept('GET', '**/metabolism/summary*', {
          statusCode: 200,
          body: {
              startDate: '2026-01-01',
              endDate: '2026-01-21',
              fat_change_kg: -1.2,
              muscle_change_kg: 0.8,
              end_fat_pct: 15.1,
              end_muscle_pct: 55.4
          }
      }).as('getMetabolismDetailed');

      cy.reload();
      cy.wait('@getMetabolismDetailed');

      cy.contains('Evolução Composição').should('exist');
  });

  it.skip('should display weight trend line chart', () => {
    cy.contains('Tendência (Histórico)').should('be.visible');
    cy.contains('Tendência (Histórico)').closest('.bg-light-bg').find('canvas').should('be.visible');
  });

  it.skip('should display consistency stacked bar chart', () => {
    cy.contains('Consistência (7 dias)').should('be.visible');
    cy.contains('Consistência (7 dias)').closest('.bg-light-bg').find('canvas').should('be.visible');
  });

  it.skip('should display last workout info', () => {
    cy.wait('@getStats');
    cy.contains('Último Treino').should('exist');
    cy.contains('Full Body').should('exist');
  });

  it.skip('should display volume chart', () => {
    cy.wait('@getStats');
    cy.contains('Volume por Categoria').scrollIntoView();
    cy.get('canvas').should('be.visible');
  });

  it.skip('should display recent PRs', () => {
    cy.wait('@getStats');
    cy.contains('Recordes Recentes').should('exist');
  });

  it.skip('should navigate to chat and back to dashboard', () => {
      cy.get('app-sidebar').contains('Chat').click();
      cy.get('app-chat', { timeout: 5000 }).should('be.visible');
      cy.get('app-dashboard').should('not.exist');

      cy.get('app-sidebar').contains('Home').click();
      cy.get('app-dashboard', { timeout: 5000 }).should('be.visible');
  });

  it('should show loading state', () => {
      cy.intercept('GET', '**/workout/stats', {
          delay: 1000,
          statusCode: 200,
          body: {}
      }).as('getStatsDelayed');

      cy.reload();
      cy.get('.animate-spin').should('be.visible');
      cy.wait('@getStatsDelayed');
      cy.get('.animate-spin').should('not.exist');
  });

  it('should display section headers', () => {
    cy.wait('@getStats');
    cy.contains('Corpo').scrollIntoView().should('be.visible');
    cy.contains('Treinos').scrollIntoView().should('be.visible');
    cy.contains('Nutrição').scrollIntoView().should('be.visible');
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
