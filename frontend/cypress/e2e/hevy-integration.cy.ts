describe('Hevy Integration - Unit E2E Tests', () => {
  let userToken: string;

  before(() => {
    cy.request('POST', '/api/user/login', {
      email: 'cypress_user@test.com',
      password: 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661'
    }).then((response) => {
      userToken = response.body.token;
    });
  });

  const setupDisconnected = () => {
    cy.intercept('GET', '/api/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: false, has_key: false, api_key_masked: null, last_sync: null }
    }).as('getStatus');
    
    cy.visit('/', {
      onBeforeLoad(win) {
        win.localStorage.setItem('jwt_token', userToken);
      }
    });
    cy.get('app-sidebar').contains('Integrações').click();
    cy.wait('@getStatus');
  };

  const setupConnected = (maskedKey = '****9999') => {
    cy.intercept('GET', '/api/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: true, has_key: true, api_key_masked: maskedKey, last_sync: '2026-01-01T10:00:00Z' }
    }).as('getStatusConnected');
    
    cy.visit('/', {
      onBeforeLoad(win) {
        win.localStorage.setItem('jwt_token', userToken);
      }
    });
    cy.get('app-sidebar').contains('Integrações').click();
    cy.wait('@getStatusConnected');
  };

  it('should show "Conectar" card when disconnected initially', () => {
    setupDisconnected();
    cy.get('app-integration-card').contains('Hevy').parents('app-integration-card')
      .within(() => {
        cy.contains('Conectar').should('be.visible');
      });
  });

  it('should transition to "Ativo" after successful connection', () => {
    setupDisconnected();

    cy.contains('Hevy').click();
    cy.get('input[placeholder*="Cole sua chave aqui"]').should('be.visible');

    cy.intercept('POST', '/api/integrations/hevy/validate', {
      statusCode: 200,
      body: { valid: true, count: 20 }
    }).as('validateKey');

    cy.intercept('POST', '/api/integrations/hevy/config', {
      statusCode: 200,
      body: { message: 'Saved' }
    }).as('saveConfig');

    cy.intercept('GET', '/api/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: true, has_key: true, api_key_masked: '****4444', last_sync: null }
    }).as('getStatusActive');

    cy.get('input[placeholder*="Cole sua chave aqui"]').type('xxxx-yyyy-4444');
    cy.contains('button', 'Conectar').click();

    cy.wait(['@validateKey', '@saveConfig', '@getStatusActive']);
    cy.contains('Conectado').should('be.visible');
    cy.contains('Conectado com sucesso!').should('be.visible');
    
    cy.get('app-hevy-config button').find('svg').first().click({force: true});
    cy.get('app-integration-card').contains('Ativo').should('be.visible');
  });

  it('should successfully run import and show results', () => {
    setupConnected('****IMPT');

    cy.contains('Hevy').click();
    
    // Mock Import
    cy.intercept('POST', '/api/integrations/hevy/import', {
      statusCode: 200,
      body: { imported: 5, skipped: 2, failed: 0 }
    }).as('runImport');

    // Mock Status update after import
    cy.intercept('GET', '/api/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: true, has_key: true, api_key_masked: '****IMPT', last_sync: '2026-01-16T15:00:00Z' }
    }).as('getStatusUpdate');

    cy.contains('button', 'Importar Treinos do Hevy').click();
    cy.wait(['@runImport', '@getStatusUpdate']);

    // Check Success feedback
    cy.contains('5 treinos importados com sucesso!').should('be.visible');
    
    // Check results table
    cy.get('app-hevy-config').within(() => {
      cy.contains('5').should('be.visible'); // Imported
      cy.contains('2').should('be.visible'); // Skipped
      cy.contains('0').should('be.visible'); // Failed
    });
  });

  it('should successfully disconnect using the multi-step confirm view', () => {
    setupConnected('****DISC');

    cy.contains('Hevy').click();
    cy.contains('button', 'Desconectar').click();
    cy.contains('Desconectar Hevy?').should('be.visible');

    cy.intercept('POST', '/api/integrations/hevy/config', {
      statusCode: 200,
      body: { message: 'Cleared' }
    }).as('clearConfig');

    cy.intercept('GET', '/api/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: false, has_key: false, api_key_masked: null, last_sync: null }
    }).as('getStatusDisconnected');

    cy.contains('button', 'Sim, desconectar').click();

    cy.wait(['@clearConfig', '@getStatusDisconnected']);
    cy.contains('button', 'Conectar').should('be.visible');
    
    cy.get('app-hevy-config button').find('svg').first().click({force: true});
    cy.get('app-integration-card').contains('Conectar').should('be.visible');
  });
});
