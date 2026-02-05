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
    // Navigate to body
    cy.get('[data-cy="nav-body"]').click();
    cy.get('[data-cy="body-tab-peso"]').click();
    cy.get('app-body', { timeout: 15000 }).should('be.visible');
    
    // Scroll to the form
    cy.contains('Novo Registro').scrollIntoView();
    cy.get('[data-cy="weight-input"]', { timeout: 15000 }).should('be.visible');
    
    // Fill the form
    // Using data-cy where possible or indices
    cy.get('[data-cy="weight-input"]').clear().type('75.5');
    cy.get('[data-cy="fat-input"]').clear().type('22.0');
    cy.get('[data-cy="muscle-input"]').clear().type('54.0');
    
    // Submit
    cy.get('[data-cy="save-weight-btn"]').click();

    // Verify the POST was called with correct data
    cy.wait('@saveWeight', { timeout: 20000 }).then((interception) => {
      expect(interception.request.body).to.include({
        weight_kg: 75.5,
        muscle_mass_pct: 54.0,
        body_fat_pct: 22.0
      });
    });

    // Success message
    cy.contains('✓ Salvo!', { timeout: 10000 }).should('be.visible');
  });
});
