describe('Metabolism Dashboard', () => {
    beforeEach(() => {
        // Match project standards: 1280x720 desktop viewport
        cy.viewport(1280, 720);

        // --- 1. Global & Startup Mocks ---
        
        // Mock User Profile
        cy.intercept('GET', '**/user/profile', {
            statusCode: 200,
            body: { email: 'test@test.com', name: 'Tester', height: 180, weight: 80, age: 30, gender: 'male' }
        }).as('getProfile');

        // Essential Sidebar/Layout Data
        cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
        cy.intercept('GET', '**/trainer/available_trainers', { body: [{ trainer_id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
        cy.intercept('GET', '**/message/history*', { body: { messages: [] } }).as('chatHistory');
        cy.intercept('GET', '**/nutrition/stats*', { body: {} }).as('getNutritionStats');
        cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
        cy.intercept('GET', '**/workout/stats*', { 
           body: { 
               current_streak_weeks: 5,
               weekly_frequency: [true, false, true, false, true, false, false],
               weekly_volume: [],
               recent_prs: [],
               total_workouts: 10,
               last_workout: null
           } 
        }).as('getWorkoutStats');
        
        // --- 2. Metabolism Specific Mocks ---

        cy.intercept('GET', '**/metabolism/summary*', {
            statusCode: 200,
            body: {
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
            }
        }).as('getMetabolism');
        
        cy.intercept('GET', '**/metabolism/insight*', {
            statusCode: 200,
            body: "Analysis of your metabolism... Insight generated.",
            headers: { 'content-type': 'text/plain' }
        }).as('getInsight');

        // --- 3. Bypass Login UI (Pattern from nutrition.cy.ts) ---
        cy.visit('/', {
            onBeforeLoad: (win) => {
                win.localStorage.setItem('jwt_token', 'fake-jwt-token');
            }
        });

        // Ensure app is ready on Dashboard
        cy.get('app-sidebar', { timeout: 10000 }).should('be.visible');
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
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
