describe('Hevy Integration - Unit E2E Tests', () => {
  const setupDisconnected = () => {
    cy.mockLogin({
      intercepts: {
        '**/integrations/hevy/status': {
          statusCode: 200,
          body: { enabled: false, has_key: false, api_key_masked: null, last_sync: null },
          alias: 'getStatus'
        }
      }
    });
    
    cy.get('app-sidebar').contains('Integrações').click();
    cy.wait('@getStatus');
  };

  const setupConnected = (maskedKey = '****9999') => {
    cy.mockLogin({
      intercepts: {
        '**/integrations/hevy/status': {
          statusCode: 200,
          body: { enabled: true, has_key: true, api_key_masked: maskedKey, last_sync: '2026-01-01T10:00:00Z' },
          alias: 'getStatusConnected'
        }
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

    cy.intercept('POST', '**/integrations/hevy/validate', {
      statusCode: 200,
      body: { valid: true, count: 20 }
    }).as('validateKey');

    cy.intercept('POST', '**/integrations/hevy/config', {
      statusCode: 200,
      body: { message: 'Saved' }
    }).as('saveConfig');

    cy.intercept('GET', '**/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: true, has_key: true, api_key_masked: '****4444', last_sync: null }
    }).as('getStatusActive');

    cy.get('input[placeholder*="Cole sua chave aqui"]').type('xxxx-yyyy-4444');
    cy.contains('button', 'Conectar').click();

    // Verify calls happen in order (or at least all happen) with increased timeout
    cy.wait('@validateKey', { timeout: 10000 });
    cy.wait('@saveConfig', { timeout: 10000 });
    cy.wait('@getStatusActive', { timeout: 10000 });
    cy.contains('Conectado').should('be.visible');
    cy.contains('Conectado com sucesso!').should('be.visible');
    
    cy.get('app-hevy-config button').find('svg').first().click({force: true});
    cy.get('app-integration-card').contains('Ativo').should('be.visible');
  });

  it('should successfully run import and show results', () => {
    setupConnected('****IMPT');

    cy.contains('Hevy').click();
    
    // Mock Import
    cy.intercept('POST', '**/integrations/hevy/import', {
      statusCode: 200,
      body: { imported: 5, skipped: 2, failed: 0 }
    }).as('runImport');

    // Mock Status update after import
    cy.intercept('GET', '**/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: true, has_key: true, api_key_masked: '****IMPT', last_sync: '2026-01-16T15:00:00Z' }
    }).as('getStatusUpdate');

    cy.contains('button', 'Importar Treinos do Hevy').click();
    
    // Split waits with explicit timeout
    cy.wait('@runImport', { timeout: 15000 });
    cy.wait('@getStatusUpdate', { timeout: 15000 });

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

    cy.intercept('POST', '**/integrations/hevy/config', {
      statusCode: 200,
      body: { message: 'Cleared' }
    }).as('clearConfig');

    cy.intercept('GET', '**/integrations/hevy/status', {
      statusCode: 200,
      body: { enabled: false, has_key: false, api_key_masked: null, last_sync: null }
    }).as('getStatusDisconnected');

    cy.contains('button', 'Sim, desconectar').click();

    // Split waits
    cy.wait('@clearConfig', { timeout: 10000 });
    cy.wait('@getStatusDisconnected', { timeout: 10000 });
    
    cy.contains('button', 'Conectar').should('be.visible');
    
    cy.get('app-hevy-config button').find('svg').first().click({force: true});
    cy.get('app-integration-card').contains('Conectar').should('be.visible');
  });
});
