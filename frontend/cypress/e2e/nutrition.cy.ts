describe('Nutrition Tracking', () => {
    const mockNutritionLogs = {
      logs: [
        {
          id: '1',
          user_email: 'test@example.com',
          date: new Date().toISOString(),
          calories: 2000,
          protein_grams: 150,
          carbs_grams: 200,
          fat_grams: 65,
          fiber_grams: 30,
          sodium_mg: 2000,
          source: 'chat'
        },
        {
          id: '2',
          user_email: 'test@example.com',
          date: new Date(Date.now() - 86400000).toISOString(), // Yesterday
          calories: 1800,
          protein_grams: 140,
          carbs_grams: 180,
          fat_grams: 60,
          source: 'chat'
        }
      ],
      total: 2,
      page: 1,
      page_size: 10,
      total_pages: 1
    };
  
    beforeEach(() => {
      // Mock Login API
      cy.intercept('POST', '**/user/login', {
          statusCode: 200,
          body: { token: 'fake-jwt-token' }
      }).as('loginRequest');

      // Mock User Profile for sidebar/guard
      cy.intercept('GET', '**/user/profile', {
          statusCode: 200,
          body: { email: 'test@example.com', name: 'Test User' }
      }).as('getUserProfile');

      // Intercept Nutrition API default
      cy.intercept('GET', '**/nutrition/list*', (req) => {
        req.reply(mockNutritionLogs);
      }).as('getNutritionLogs');

      cy.intercept('GET', '**/nutrition/stats', (req) => {
          req.reply({
              today: mockNutritionLogs.logs[0],
              weekly_adherence: [true, true, false, false, false, false, false],
              last_7_days: [],
              avg_daily_calories: 1900,
              avg_protein: 145,
              total_logs: 2
          });
      }).as('getNutritionStats');
      
      // Mock Workout Stats (Required for Dashboard to load)
      cy.intercept('GET', '**/workout/stats', {
          statusCode: 200,
          body: {
             current_streak_weeks: 5,
             weekly_frequency: [true, false, true, false, true, false, false],
             weekly_volume: [],
             recent_prs: [],
             total_workouts: 10,
             last_workout: null
          }
      }).as('getWorkoutStats');
      
      // Perform login
      
      // Perform login
      cy.login('test@example.com', 'password123'); // This uses the mocked endpoint now if cy.login uses cy.request or UI
    });
  
    it('should navigate to nutrition page from sidebar', () => {
      cy.get('[data-cy="nav-nutrition"]').click();
      // cy.url().should('include', '/nutrition'); // Skipping URL check as we use signal-based nav
      cy.get('h1').contains('Histórico Nutricional');
    });
  
    it('should display nutrition logs in timeline', () => {
      cy.get('[data-cy="nav-nutrition"]').click();
      cy.wait('@getNutritionLogs');
  
      // Check for log cards
      cy.contains('2000').should('be.visible'); // Calories
      cy.contains('kcal').should('be.visible');
      cy.contains('150g').should('be.visible'); // Protein in legend
      
      // Verify Date Format (Portuguese)
      // We expect "domingo, 11 de janeiro de 2026" or similar based on mock date
      // Mock date is new Date().toISOString()
      const today = new Date();
      const month = today.toLocaleString('pt-BR', { month: 'long' });
      // Regex to match e.g. "domingo, 11 de janeiro de 2026" (case insensitive)
      // The day might vary, but month should be present
      cy.get('.text-xs.uppercase.font-bold').invoke('text').should('match', new RegExp(month, 'i'));
      
      // Also check specific structure: "day_name, day de month de year"
      // Simplest check: ensure it contains "de" and the current year
      cy.get('.text-xs.uppercase.font-bold').invoke('text').should('include', today.getFullYear().toString());
    });

    it('should show micros if available', () => {
        cy.get('[data-cy="nav-nutrition"]').click();
        cy.wait('@getNutritionLogs');
        cy.contains('Fibras: 30g').should('be.visible');
        cy.contains('Sódio: 2000mg').should('be.visible');
    });

    it('should show empty state if no logs', () => {
        cy.intercept('GET', '**/nutrition/list*', {
            logs: [], total: 0, page: 1, page_size: 10, total_pages: 0
        }).as('getEmptyLogs');

        cy.get('[data-cy="nav-nutrition"]').click();
        cy.wait('@getEmptyLogs');

        cy.contains('Nenhum registro encontrado').should('be.visible');
    });

    it('should display nutrition widgets on dashboard', () => {
        // Reload to ensure component re-initializes and fires requests within this test block
        cy.reload();
        
        // Now we can safely wait for the requests
        cy.wait(['@getNutritionStats', '@getWorkoutStats']);
        
        // Check for widget titles
        cy.contains('Macros de Hoje', { timeout: 10000 }).scrollIntoView().should('be.visible');
        cy.contains('Aderência (Dieta)').scrollIntoView().should('be.visible');
        cy.contains('Última Refeição').scrollIntoView().should('be.visible');
        cy.contains('Calorias (7 dias)').scrollIntoView().should('be.visible');

        // Check content
        cy.contains('2000').scrollIntoView().should('be.visible'); // Today cal inside doughnut
        cy.contains('150g P').scrollIntoView().should('be.visible');
    });
  });
