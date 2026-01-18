/**
 * Body Composition Page Tests
 * 
 * NOTE: This app uses signals-based navigation (NavigationService), NOT Angular Router.
 * The URL remains at localhost:3000/ - views are swapped dynamically.
 * 
 * Strategy: All backend calls are mocked BEFORE any navigation.
 */
describe('Body Composition Page', () => {
  // Shared mock data
  const mockStats = {
    latest: {
      date: '2026-01-01',
      weight_kg: 80.5,
      body_fat_pct: 20.5,
      muscle_mass_pct: 40.0,
      body_water_pct: 55.0,
      visceral_fat: 10,
      bmr: 1800,
      user_email: 'cypress_user@test.com'
    },
    weight_trend: [
      { date: '2025-12-25', weight: 81.0 },
      { date: '2026-01-01', weight: 80.5 }
    ]
  };

  const mockHistory = [
    {
      date: '2026-01-01',
      weight_kg: 80.5,
      body_fat_pct: 20.5,
      muscle_mass_pct: 40.0,
      body_water_pct: 55.0,
      visceral_fat: 10,
      bmr: 1800,
      user_email: 'cypress_user@test.com'
    }
  ];

  beforeEach(() => {
    // Pass ALL intercepts to mockLogin so they are active BEFORE the visit
    cy.mockLogin({
      intercepts: {
        '**/weight/stats*': { body: mockStats, alias: 'getStats' },
        '**/weight?limit=*': { body: mockHistory, alias: 'getHistory' },
        'POST **/weight': { statusCode: 200, body: { message: 'OK' }, alias: 'saveWeight' },
        'DELETE **/weight/*': { statusCode: 200, body: { message: 'Deleted' }, alias: 'deleteWeight' }
      }
    });
  });

  it('navigates to body composition page via sidebar', () => {
    // Navigate to body composition
    cy.get('[data-cy="nav-body-composition"]').click();
    cy.get('app-body-composition', { timeout: 15000 }).should('be.visible');
    cy.get('h1').should('contain', 'Composição Corporal');
  });

  it('displays hero card content when data exists', () => {
    cy.get('[data-cy="nav-body-composition"]').click();
    // Re-verify visibility and content without strict wait if possible, or wait with longer timeout
    cy.get('[data-cy="latest-weight"]', { timeout: 15000 }).should((el) => {
      const text = el.text();
      expect(text).to.match(/80[,.]5/); // Flexible check for decimal separator
    });
    // Flexible check for decimal separator (can be . or ,)
    cy.get('[data-cy="latest-body-fat"]').should((el) => {
      const text = el.text();
      expect(text).to.match(/20[,.]50/);
    });
  });

  it('displays history table', () => {
    cy.get('[data-cy="nav-body-composition"]').click();
    cy.wait('@getHistory');
    cy.get('[data-cy="composition-history"]').scrollIntoView();
    cy.get('[data-cy="composition-history"]').should('exist');
    cy.get('[data-cy="history-entry"]').should('have.length.at.least', 1);
  });

  it('validates strictly numeric inputs (Firefox bug)', () => {
    cy.get('[data-cy="nav-body-composition"]').click();
    cy.wait('@getStats');
    
    // Scroll to the manual entry form and wait for element to be ready
    cy.contains('Adicionar Registro Manual').scrollIntoView();
    cy.get('[data-cy="weight-input"]', { timeout: 10000 }).should('be.visible');
    
    // Clear and type alphanumeric - only numbers should remain
    cy.get('[data-cy="weight-input"]').clear().type('12abc34');
    cy.get('[data-cy="weight-input"]').should('have.value', '1234');
    
    // Test decimal input
    cy.get('[data-cy="weight-input"]').clear().type('10.5');
    cy.get('[data-cy="weight-input"]').should('have.value', '10.5');

    // Test prevent multiple dots
    cy.get('[data-cy="weight-input"]').clear().type('10.5.5');
    cy.get('[data-cy="weight-input"]').should('have.value', '10.55');
  });

  it('allows editing an existing entry', () => {
    cy.get('[data-cy="nav-body-composition"]').click();
    cy.wait(['@getStats', '@getHistory']);
    
    // Scroll to history section to find edit button
    cy.get('[data-cy="composition-history"]').scrollIntoView();
    cy.get('[data-cy="edit-btn"]', { timeout: 10000 }).should('be.visible');
    
    // Click edit button on first entry
    cy.get('[data-cy="edit-btn"]').first().click();
    
    // Scroll up to form to check the values
    cy.contains('Adicionar Registro Manual').scrollIntoView();
    
    // Form should be populated with entry values
    cy.get('[data-cy="weight-input"]').should('have.value', '80.5');
    
    // Modify and save
    cy.get('[data-cy="weight-input"]').clear().type('82');
    cy.contains('button', 'Salvar Registro').click();
    
    cy.wait('@saveWeight');
    
    // Success message shows inline - it may take a moment to appear due to Angular change detection
    cy.contains('Registro salvo com sucesso!', { timeout: 5000 }).should('exist');
  });

  it('allows deleting an entry', () => {
    cy.get('[data-cy="nav-body-composition"]').click();
    cy.wait(['@getStats', '@getHistory']);
    
    // Scroll to history section
    cy.get('[data-cy="composition-history"]').scrollIntoView();
    cy.get('[data-cy="delete-btn"]', { timeout: 10000 }).should('be.visible');
    
    // Stub window.confirm to return true
    cy.on('window:confirm', () => true);
    
    // Click delete button
    cy.get('[data-cy="delete-btn"]').first().click();
    
    cy.wait('@deleteWeight');
    
    // After delete, the page reloads data - verify the request was made
    // (No success message for delete in current implementation)
  });
});
