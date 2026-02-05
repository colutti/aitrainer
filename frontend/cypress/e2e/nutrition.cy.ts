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
        cy.viewport(1280, 720);
        cy.mockLogin({
            intercepts: {
                '**/nutrition/list*': { statusCode: 200, body: mockNutritionLogs, alias: 'getNutritionLogs' },
                '**/nutrition/stats': {
                    statusCode: 200,
                    body: {
                        today: mockNutritionLogs.logs[0],
                        weekly_adherence: [true, true, false, false, false, false, false],
                        last_7_days: [],
                        avg_daily_calories: 1900,
                        avg_protein: 145,
                        total_logs: 2,
                        last_14_days: []
                    },
                    alias: 'getNutritionStats'
                },
                '**/weight/stats*': { statusCode: 200, body: { latest: null, weight_trend: [] }, alias: 'getWeightStats' },
                '**/weight': { statusCode: 200, body: [], alias: 'getWeightHistory' },
                '**/weight?*': { statusCode: 200, body: [], alias: 'getWeightHistoryQuery' },
                '**/metabolism/summary*': { 
                    statusCode: 200, 
                    body: { 
                        tdee: 2200, 
                        daily_target: 2000, 
                        weight_trend: [], 
                        consistency: [] 
                    }, 
                    alias: 'getMetabolismSummary' 
                },
                '**/workout/stats': { statusCode: 200, body: { streak: 0, frequency: [] }, alias: 'getWorkoutStats' }
            }
        });
        
        cy.on('window:console', (msg) => {
            console.log('BROWSER_CONSOLE:', msg);
        });
    });
  
    it('should navigate to nutrition page from sidebar', () => {
        cy.get('[data-cy="nav-body"]').click();
        cy.wait('@getNutritionLogs');
        cy.wait('@getNutritionStats');
        cy.get('[data-cy="body-tab-nutricao"]').should('be.visible').click();
        cy.get('h3').contains('Novo Registro').should('be.visible');
    });
  
    it('should display nutrition logs in list', () => {
        cy.get('[data-cy="nav-body"]').click();
        
        cy.wait('@getNutritionLogs');
        cy.wait('@getNutritionStats');
        
        // Switch to Nutrition tab
        cy.get('[data-cy="body-tab-nutricao"]').should('be.visible').click();
        
        // Verify tab is active (check for primary color class)
        cy.get('[data-cy="body-tab-nutricao"]').should('have.class', 'text-primary');
        
        // Ensure form is visible (Loading done)
        cy.get('.animate-spin', { timeout: 10000 }).should('not.exist');
        cy.get('h3').contains('Novo Registro TESTE').should('be.visible');
        
        // Debug: Check if form inputs are rendered
        cy.get('[data-cy="calories-input"]').should('exist');

        // CHECK DEBUG LENGTH
        cy.get('[data-cy="debug-logs-len"]', { timeout: 10000 }).should('be.visible').then($el => {
           cy.log('DEBUG LEN TEXT: ' + $el.text());
        });

        cy.get('[data-cy="nutrition-log-item"]').should('have.length', 2);
    });

    it('should show empty state if no logs', () => {
        cy.intercept('GET', '**/nutrition/list*', {
            body: { logs: [], total: 0, page: 1, page_size: 10, total_pages: 0 },
            statusCode: 200
        }).as('getEmptyLogs');

        cy.get('[data-cy="nav-body"]').click();
        
        cy.wait('@getEmptyLogs');
        
        cy.get('[data-cy="body-tab-nutricao"]').should('be.visible').click();
        cy.get('.animate-spin', { timeout: 10000 }).should('not.exist');
        
        cy.get('[data-cy="nutrition-empty-state"]').should('be.visible');
    });

    it('should delete a nutrition log', () => {
        cy.get('[data-cy="nav-body"]').click();
        cy.wait('@getNutritionLogs'); 
        
        cy.get('[data-cy="body-tab-nutricao"]').should('be.visible').click();
        
        cy.get('[data-cy="nutrition-log-item"]').should('have.length', 2);

        // Intercept DELETE
        cy.intercept('DELETE', '**/nutrition/1', {
            statusCode: 200,
            body: { message: 'Nutrition log deleted successfully' }
        }).as('deleteLog');

        // Mock re-fetch after deletion (return only 1 item)
        cy.intercept('GET', '**/nutrition/list*', {
            statusCode: 200,
            body: {
                logs: [mockNutritionLogs.logs[1]],
                total: 1, page: 1, page_size: 10, total_pages: 1
            }
        }).as('getLogsAfterDelete');

        cy.on('window:confirm', () => true);

        // Click delete
        cy.get('[data-cy="nutrition-log-item"]').first().find('[data-cy="delete-nutrition-log"]').click({ force: true });

        cy.wait('@deleteLog');
        cy.wait('@getLogsAfterDelete');

        cy.get('[data-cy="nutrition-log-item"]').should('have.length', 1);
        cy.get('[data-cy="nutrition-log-item"]').first().contains(/1[.,]?800/);
    });
});
