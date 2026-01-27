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
        }
      }
    });
  });

  it('should display the average calories widget on the dashboard', () => {
    // The nutrition stats are loaded automatically by the dashboard component
    // Give Angular time to render the widget (stats signal updates)
    cy.wait(1000);

    // Check for the widget - it should exist in the DOM
    cy.get('app-widget-average-calories', { timeout: 10000 }).should('exist');

    // Scroll the widget into view so we can verify its contents
    cy.get('app-widget-average-calories').scrollIntoView();

    // Verify contents
    cy.get('app-widget-average-calories').within(() => {
      cy.contains('Médias de Consumo').should('be.visible');
      cy.contains('Últimos 7 dias').should('be.visible');
      // Values may be formatted with locale separator (pt-BR uses '.' as thousands separator)
      // So 2250.5 → 2.251 or 2251 depending on pipe format
      cy.contains(/2[,.;]?251/).should('exist');
      cy.contains('Últimos 14 dias').should('be.visible');
      cy.contains(/2[,.;]?100/).should('exist');
    });
  });

  it('should verify widget renders with correct data structure', () => {
    // Additional test to verify the widget component receives correct props
    cy.wait(1000);

    // Check widget renders
    cy.get('app-widget-average-calories').should('exist');

    // Verify the widget contains expected text labels
    cy.get('app-widget-average-calories').within(() => {
      cy.contains('Médias de Consumo').should('exist');
      cy.contains('Últimos 7 dias').should('exist');
      cy.contains('Últimos 14 dias').should('exist');
      cy.contains('KCAL').should('exist');
    });

    // Scroll widget into view and verify values are visible
    cy.get('app-widget-average-calories').scrollIntoView();
    cy.get('app-widget-average-calories').within(() => {
      cy.contains(/2[,.;]?251/).should('be.visible');
      cy.contains(/2[,.;]?100/).should('be.visible');
    });
  });
});
