export const COMMON_MOCKS = {
  trainerProfile: { trainer_type: 'atlas' },
  availableTrainers: [{ trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png' }],
  weightStats: { latest: null, weight_trend: [] },
  workoutStats: { streak: 0, frequency: [] },
  nutritionStats: { daily_target: 2000, current_macros: {} },
  chatHistory: [],
  metabolismSummary: {
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
    weight_trend: []
  },
  userProfile: { 
    email: 'cypress_user@test.com', 
    gender: 'Masculino', 
    age: 30, 
    weight: 80, 
    height: 180, 
    goal: 'Ganhar massa' 
  }
};

export const setupCommonIntercepts = () => {
    // 1. CATCH-ALL SAFETY NET (Defined FIRST so it's overridden by specific mocks)
    // Any request not matched by later intercepts will fall back to this.
    // We return 404 to prevent 401 Unauthorized from backend execution, which triggers logout.
    cy.intercept('**', (req) => {
        // Check for root path (allow it)
        try {
            const urlObj = new URL(req.url);
            if (urlObj.pathname === '/' || urlObj.pathname === '/index.html') return;
        } catch (e) {}

        // Allow static assets (js, css, html) to pass through if not mocked elsewhere
        // But block API calls. Also catch requests with NO extension (usually API)
        if (req.url.includes('/api/') || req.url.includes('graphql') || req.url.includes('backend') || !req.url.split('/').pop()?.includes('.')) {
            const msg = `⚠️ UNMOCKED API REQUEST BLOCKED: ${req.method} ${req.url}`;
            // Log but don't throw, just block.
            console.error(msg);
            req.reply({ statusCode: 404, body: { error: 'Unmocked request blocked by test safety net' } });
        }
    }).as('unmockedFallback');

    // Prevent 404s/Hangs for Assets (Fonts, Images)
    cy.intercept('GET', '**/assets/**', { statusCode: 200, body: '' }).as('assets');

  // Load fixtures
  cy.intercept('GET', '**/trainer/trainer_profile', { body: COMMON_MOCKS.trainerProfile }).as('getTrainerProfile');
  cy.intercept('POST', '**/trainer/chat', { body: { response: 'Mock AI response' } }).as('chatResponse');
  cy.intercept('GET', '**/trainer/available_trainers', { body: COMMON_MOCKS.availableTrainers }).as('availableTrainers');
  cy.intercept('GET', '**/weight/stats*', { body: COMMON_MOCKS.weightStats }).as('getWeightStats');
  cy.intercept('GET', '**/workout/stats', { body: COMMON_MOCKS.workoutStats }).as('getWorkoutStats');
  cy.intercept('GET', '**/nutrition/stats', { body: COMMON_MOCKS.nutritionStats }).as('getNutritionStats');
  // Dashboard & Profile
  cy.intercept('GET', '**/metabolism/summary*', { body: COMMON_MOCKS.metabolismSummary }).as('getMetabolismSummary');
  cy.intercept('GET', '**/user/profile', { body: COMMON_MOCKS.userProfile }).as('userProfile');
  cy.intercept('POST', '**/user/logout', { statusCode: 200 }).as('logout');
  cy.intercept('GET', '**/weight?limit=*', { body: [] }).as('getWeightHistory');
  cy.intercept('GET', '**/weight/stats', { body: COMMON_MOCKS.weightStats }).as('getWeightStats');
  
  // Integrations - Hevy
  cy.intercept('GET', '**/integrations/hevy/status', { 
    body: { enabled: false, has_key: false, api_key_masked: null, last_sync: null } 
  }).as('hevyStatusDefault');
  
  cy.intercept('GET', '**/integrations/hevy/count', { 
    body: { count: 0 } 
  }).as('hevyCountDefault');

  cy.intercept('GET', '**/integrations/hevy/webhook/config', { 
    body: { has_webhook: false } 
  }).as('hevyWebhookDefault');
  
  // Telegram - Use broader wildcard to catch /api/telegram or /telegram
  cy.intercept('GET', '**/telegram/status', { 
    body: { linked: false } 
  }).as('telegramStatusDefault');
}
