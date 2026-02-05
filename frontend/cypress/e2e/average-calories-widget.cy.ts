describe('Average Calories Widget', () => {
  beforeEach(() => {
    // We use mockLogin which handles the JWT token and the initial visit
    cy.mockLogin({
      intercepts: {
        'GET **/nutrition/stats': {
          statusCode: 200,
          body: {
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
            endDate: '2026-01-27'
          },
          alias: 'getNutritionStats'
        },
        'GET **/nutrition/list*': {
          statusCode: 200,
          body: {
            logs: [],
            total: 0,
            total_pages: 1,
            page: 1,
            page_size: 10
          },
          alias: 'getNutritionLogs'
        },
        'GET **/metabolism/summary*': {
          statusCode: 200,
          body: {
            tdee: 2800,
            daily_target: 2500,
            weight_trend: [],
            consistency: [],
            confidence: 'high',
            startDate: '2026-01-20',
            endDate: '2026-01-27',
            status: 'maintenance',
            energy_balance: 0
          },
          alias: 'getMetabolismSummary'
        },
        'GET **/weight/history': {
          statusCode: 200,
          body: [],
          alias: 'getWeightHistory'
        },
        'GET **/weight/stats': {
          statusCode: 200,
          body: {
            weight_trend: [],
            fat_trend: [],
            muscle_trend: [],
            latest: null
          },
          alias: 'getWeightStats'
        }
      }
    });
  });

  it('should display the average calories widget in the Body Statistics tab', () => {
    // Navigate to Body tab
    cy.get('[data-cy="nav-body"]').click();
    
    // Wait for all critical stats to load to avoid race conditions
    cy.wait(['@getNutritionStats', '@getMetabolismSummary', '@getWeightStats']);

    // Ensure we are on Statistics tab
    cy.get('[data-cy="body-tab-estatisticas"]').click();

    // Check for the average calories widget
    // It should rendered because nutritionStats is truthy
    cy.get('app-widget-average-calories', { timeout: 15000 })
      .scrollIntoView()
      .should('be.visible');

    // Verify contents using data-test attributes
    cy.get('[data-test="avg-7-days"]').should('contain', '2');
    cy.get('[data-test="avg-7-days"]').should('contain', '251'); // 2250.5 rounded
    
    cy.get('[data-test="avg-14-days"]').should('contain', '2');
    cy.get('[data-test="avg-14-days"]').should('contain', '100'); // 2100.2 rounded
  });
});
