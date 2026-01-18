/**
 * Body Composition - Muscle Mass Bug Test
 * 
 * This test verifies that muscle mass values are correctly saved and displayed.
 * Uses mocked backend to ensure consistent results.
 */
describe('Body Composition - Manual Entry Bug', () => {
  beforeEach(() => {
    // Pass ALL intercepts to mockLogin
    cy.mockLogin({
      intercepts: {
        '**/weight?limit=*': { body: [], alias: 'getHistory' },
        'POST **/weight': { statusCode: 200, body: { message: 'Weight saved' }, alias: 'saveWeight' },
        '**/weight/stats*': { body: { latest: null, weight_trend: [] }, alias: 'getStats' }
      }
    });
  });

  it('should save and display muscle mass value correctly', () => {
    // Navigate to body composition
    cy.get('[data-cy="nav-body-composition"]').click();
    cy.get('app-body-composition', { timeout: 15000 }).should('be.visible');
    
    // Scroll to the form and wait for input to be visible
    cy.contains('Adicionar Registro Manual').scrollIntoView();
    cy.get('[data-cy="weight-input"]', { timeout: 15000 }).should('be.visible');
    
    // Fill the form
    cy.get('input[type="date"]').clear().type('2026-01-12');
    cy.get('[data-cy="weight-input"]').clear().type('75.5');
    cy.get('[data-cy="fat-input"]').clear().type('22.0');
    
    // Fill muscle (need to find the input - third number input after weight/fat)
    cy.get('input[type="number"]').eq(2).clear().type('54.0');  // Muscle is 3rd input
    
    // Fill water
    cy.get('input[type="number"]').eq(3).clear().type('52.0');

    // Submit
    cy.contains('button', 'Salvar Registro').click();

    // Verify the POST was called with correct data
    cy.wait('@saveWeight', { timeout: 20000 }).then((interception) => {
      expect(interception.request.body).to.include({
        weight_kg: 75.5,
        muscle_mass_pct: 54.0,
        body_fat_pct: 22.0,
        body_water_pct: 52.0
      });
    });

    // Success message shows inline (not a global toast)
    cy.contains('Registro salvo com sucesso!', { timeout: 10000 }).should('be.visible');
  });
});
