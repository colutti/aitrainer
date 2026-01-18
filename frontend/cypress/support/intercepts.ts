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

export function setupCommonIntercepts(): void {
  cy.intercept('GET', '**/trainer/trainer_profile', { body: COMMON_MOCKS.trainerProfile }).as('trainerProfile');
  cy.intercept('GET', '**/trainer/available_trainers', { body: COMMON_MOCKS.availableTrainers }).as('availableTrainers');
  cy.intercept('GET', '**/weight/stats*', { body: COMMON_MOCKS.weightStats }).as('getWeightStats');
  cy.intercept('GET', '**/workout/stats', { body: COMMON_MOCKS.workoutStats }).as('getWorkoutStats');
  cy.intercept('GET', '**/nutrition/stats', { body: COMMON_MOCKS.nutritionStats }).as('getNutritionStats');
  cy.intercept('GET', '**/message/history*', { body: COMMON_MOCKS.chatHistory }).as('chatHistory');
  cy.intercept('GET', '**/metabolism/summary*', { body: COMMON_MOCKS.metabolismSummary }).as('getMetabolismSummary');
  cy.intercept('GET', '**/user/profile', { body: COMMON_MOCKS.userProfile }).as('userProfile');
}
