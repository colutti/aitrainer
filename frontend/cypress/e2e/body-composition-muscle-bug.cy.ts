describe('Body Composition - Manual Entry Bug', () => {
  beforeEach(() => {
    cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    // Navigate to body composition via sidebar click
    cy.contains('Composição').click();
    cy.wait(2000);
  });

  it('should save and display muscle mass value correctly', () => {
    // Scroll to the form
    cy.contains('Adicionar Registro Manual').scrollIntoView();
    cy.wait(500);

    // Fill date
    cy.get('input[type="date"]').clear().type('2026-01-12');
    
    // Fill weight
    cy.get('input[type="number"][step="0.1"]').eq(0).clear().type('75.5');
    
    // Fill fat
    cy.get('input[type="number"][step="0.1"]').eq(1).clear().type('22.0');
    
    // Fill muscle
    cy.get('input[type="number"][step="0.1"]').eq(2).clear().type('54.0');
    
    // Fill water
    cy.get('input[type="number"][step="0.1"]').eq(3).clear().type('52.0');

    // Submit the form
    cy.contains('button', 'Salvar Registro').click();

    // Wait for data to be saved and page to reload
    cy.wait(5000);

    // Scroll to history table
    cy.contains('Histórico Detalhado').scrollIntoView();
    cy.wait(500);

    // Verify the muscle mass value appears in the table (Brazilian locale uses comma)
    cy.get('table').should('contain', '54,00%');
  });
});
