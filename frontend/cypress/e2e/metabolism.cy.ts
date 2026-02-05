describe('Metabolism Dashboard', () => {
    beforeEach(() => {
        // Match project standards: 1280x720 desktop viewport
        cy.viewport(1280, 720);

        const metabolismSummary = {
            confidence: 'high',
            logs_count: 14,
            tdee: 2200,
            daily_target: 2000,
            avg_calories: 1800,
            start_weight: 80.0,
            end_weight: 79.5,
            weight_change_per_week: -0.5,
            goal_weekly_rate: -0.5,
            status: 'deficit',
            energy_balance: -200,
            startDate: '2023-01-01',
            endDate: '2023-01-14',
            consistency_score: 95,
            confidence_reason: 'Muitos dados',
            weight_trend: [
                { date: '2023-01-01', weight: 80.0, trend: 80.0 },
                { date: '2023-01-02', weight: 79.8, trend: 79.9 }
            ],
            consistency: [],
            weight_logs_count: 10,
            logs_count: 14,
            outliers_count: 0
        };

        // 100% Mocked Login
        cy.mockLogin({
            intercepts: {
                // Dashboard chama com weeks=100, Metabolism chama com weeks=3
                '**/metabolism/summary?weeks=100': { statusCode: 200, body: metabolismSummary, alias: 'getDashboardMetabolism' },
                '**/metabolism/summary?weeks=3': { statusCode: 200, body: metabolismSummary, alias: 'getMetabolismDefault' },
                '**/metabolism/summary?weeks=8': { statusCode: 200, body: metabolismSummary, alias: 'getMetabolism8Weeks' },
                '**/nutrition/stats': { 
                    statusCode: 200, 
                    body: { 
                        today: null, 
                        avg_daily_calories: 1800, 
                        avg_daily_calories_14_days: 1850,
                        last_14_days: [] 
                    }, 
                    alias: 'getNutritionStats' 
                },
                '**/nutrition/list*': { statusCode: 200, body: { logs: [], total: 0, total_pages: 0 }, alias: 'getNutritionLogs' },
                '**/weight/stats': { 
                    statusCode: 200, 
                    body: { 
                        weight_trend: [], 
                        fat_trend: [], 
                        muscle_trend: [] 
                    }, 
                    alias: 'getWeightStats' 
                },
                '**/weight': { statusCode: 200, body: [], alias: 'getWeightHistory' },
                '**/weight?*': { statusCode: 200, body: [], alias: 'getWeightHistoryQuery' },
                '**/metabolism/insight*': {
                    statusCode: 200,
                    body: "Analysis of your metabolism... Insight generated.",
                    headers: { 'content-type': 'text/plain' },
                    alias: 'getInsight'
                }
            }
        });
    });

    it('should display the metabolism dashboard components', () => {
        // Step 1: Wait for app stability after login
        cy.get('app-dashboard', { timeout: 15000 }).should('be.visible');

        // Step 2: Navigate to Body view
        cy.get('[data-cy="nav-body"]').should('be.visible').click();

        // Step 3: Wait for all data to load
        cy.wait(['@getMetabolismDefault', '@getNutritionStats', '@getWeightStats']);
        
        // Wait for internal loading signal to disappear
        cy.get('.animate-spin', { timeout: 10000 }).should('not.exist');

        // Step 4: Verify Header
        cy.get('h1').should('contain', 'Corpo');

        // Step 5: Verify Specific Data Elements
        // Check in app-widget-tdee-summary
        cy.get('[data-cy="daily-target"]', { timeout: 10000 }).scrollIntoView().should('be.visible');
        cy.get('[data-cy="daily-target"]').invoke('text').should('match', /2[.,]000/);
        cy.get('[data-cy="tdee-value"]').invoke('text').should('match', /2[.,]200/);
        
        // NEW Components Check
        cy.get('app-widget-data-quality').scrollIntoView().should('be.visible');
        
        // Step 6: Verify Period Selector Interaction using data-cy
        cy.get('[data-cy="period-btn-8"]').scrollIntoView().should('be.visible').click();
        cy.wait('@getMetabolism8Weeks');
        cy.get('app-widget-data-quality').should('be.visible');
        
        // Step 7: Verify Layout Sections
        // 'Novo Registro' is in Nutrition tab, not here.
        cy.get('app-widget-tdee-summary').should('exist');
    });
});
