describe.skip('Metabolism Dashboard', () => {
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
            endDate: '2023-01-14'
        };

        // 100% Mocked Login
        cy.mockLogin({
            intercepts: {
                // Dashboard chama com weeks=100, Metabolism chama com weeks=3
                '**/metabolism/summary?weeks=100': { statusCode: 200, body: metabolismSummary, alias: 'getDashboardMetabolism' },
                '**/metabolism/summary?weeks=3': { statusCode: 200, body: metabolismSummary, alias: 'getMetabolism' },
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
        cy.get('app-dashboard').should('be.visible');

        // Step 2: Navigate to Metabolism view
        cy.get('[data-cy="nav-metabolism"]').should('be.visible').click({ force: true });

        // Step 3: Handle @defer loading (app uses @defer with 500ms min loading)
        cy.get('app-metabolism', { timeout: 15000 }).should('be.visible');

        // Step 4: Verify Header & Wait for Data
        cy.get('h1').should('contain', 'Seu Metabolismo');
        cy.wait('@getMetabolism');
        
        // Wait for internal loading signal to disappear
        cy.get('.animate-spin', { timeout: 10000 }).should('not.exist');

        // Step 5: Verify Specific Data Elements
        cy.get('[data-cy="logs-count"]').should('contain', '14');
        cy.get('[data-cy="daily-target"]').should('contain', '2000');
        cy.get('[data-cy="tdee-value"]').should('contain', '2200');
        
        // Step 6: Verify Layout Sections
        cy.get('[data-cy="trainer-analysis-header"]').should('exist');
        cy.get('[data-cy="transparency-title"]').should('exist');
        
        // Verify AI Insight content from mock
        cy.get('markdown').should('not.be.empty');
        cy.get('markdown').should('contain', 'Analysis');
    });
});
