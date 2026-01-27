export const COMMON_MOCKS = {
  trainerProfile: { trainer_type: 'atlas' },
  availableTrainers: [{ trainer_id: 'atlas', name: 'Atlas', avatar_url: '/assets/atlas.png' }],
  weightStats: { latest: null, weight_trend: [] },
  workoutStats: { streak: 0, frequency: [] },
  nutritionStats: {
    today: null,
    weekly_adherence: [true, false, true, true, false, true, true],
    last_7_days: [],
    last_14_days: [],
    avg_daily_calories: 2250.5,
    avg_daily_calories_14_days: 2100.2,
    avg_protein: 150.0,
    total_logs: 20,
    macro_targets: { protein: 200, carbs: 300, fat: 80 },
    daily_target: 2500,
    stability_score: 85,
    startDate: '2026-01-20',
    endDate: '2026-01-27',
    tdee: null,
    consistency_score: null,
    weight_logs_count: null
  },
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
    weight_trend: [],
    consistency: [],
    goal_type: 'deficit',
    expenditure_trend: 'stable',
    fat_change_kg: 0,
    muscle_change_kg: 0,
    startDate: '2026-01-20',
    endDate: '2026-01-27'
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
    cy.intercept('GET', '**/user/me', { body: { email: COMMON_MOCKS.userProfile.email, role: 'user' } }).as('userMe');
    cy.intercept('POST', '**/user/logout', { statusCode: 200 }).as('logout');
    cy.intercept('GET', '**/weight?limit=*', { body: [] }).as('getWeightHistory');
    cy.intercept('GET', '**/weight/stats', { body: COMMON_MOCKS.weightStats }).as('getWeightStats');

    // Prevent 404s/Hangs for Assets (Fonts, Images)
    cy.intercept('GET', '**/assets/**', { statusCode: 200, body: '' }).as('assets');

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
