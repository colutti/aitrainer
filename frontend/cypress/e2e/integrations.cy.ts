describe('Integrations Page', () => {
  beforeEach(() => {
    // Mock login endpoint
    cy.intercept('POST', '**/user/login', {
       statusCode: 200,
       body: { token: 'mock-token' }
    }).as('login');
    
    // Mock Profile
    cy.intercept('GET', '**/user/profile', {
        email: 'test@example.com', gender: 'M', age: 30, weight: 80, height: 180, goal: 'Gain', goal_type: 'gain', weekly_rate: 0.5
    }).as('getProfile');

    // Integration Mocks
    cy.intercept('GET', '**/integrations/hevy/status', {
        enabled: false, has_key: false, api_key_masked: null, last_sync: null
    }).as('getStatus');
    
    cy.intercept('POST', '**/integrations/hevy/validate', {
        valid: true, count: 52
    }).as('validateKey');

    cy.intercept('POST', '**/integrations/hevy/config', {
        message: 'Saved'
    }).as('saveConfig');
    
    cy.login('test@example.com', 'password');
  });

  it('should navigate to integrations and configure Hevy', () => {
    // Check Sidebar loaded
    cy.get('app-sidebar').should('be.visible');
    
    // Debug: Check if button exists
    cy.get('app-sidebar').contains('Integrações').should('exist').click();
    
    // Check page loaded
    cy.get('app-integrations').should('exist');
    cy.contains('h1', 'Integrações').should('be.visible');
    
    // Check Cards
    cy.contains('Hevy').should('be.visible');
    cy.contains('Não configurado').should('be.visible');
    
    // Toggle Hevy
    cy.contains('Hevy').parents('app-integration-card').find('input[type="checkbox"]').click({force: true});
    
    // Config modal
    cy.get('app-hevy-config').should('be.visible');
    cy.contains('Configurar Hevy').should('be.visible');
    
    // Input/Save
    cy.get('input[placeholder*="Cole sua chave"]').type('test-uuid-key');
    cy.contains('button', 'Salvar').click();
    
    // Wait
    cy.wait('@validateKey');
    cy.wait('@saveConfig');
    
    // Verify
    cy.contains('Conectado').should('be.visible');
  });
});
