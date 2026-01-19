describe('Telegram Integration', () => {
  const setupDisconnected = () => {
    cy.mockLogin({
      intercepts: {
        '**/api/telegram/status': {
          statusCode: 200,
          body: { linked: false },
          alias: 'getTelegramStatus'
        },
        '**/integrations/hevy/status': {
          statusCode: 200,
          body: { enabled: false, hasKey: false, apiKeyMasked: null, lastSync: null },
          alias: 'getHevyStatus'
        }
      }
    });
    cy.get('app-sidebar').contains('Integrações').click();
    cy.wait(['@getTelegramStatus', '@getHevyStatus'], { timeout: 10000 });
  };

  const setupConnected = () => {
    cy.mockLogin({
      intercepts: {
        '**/api/telegram/status': {
          statusCode: 200,
          body: { 
            linked: true, 
            telegram_username: '@testuser',
            linked_at: '2026-01-19T20:00:00Z'
          },
          alias: 'getTelegramStatusConnected'
        },
        '**/integrations/hevy/status': {
          statusCode: 200,
          body: { enabled: false, hasKey: false, apiKeyMasked: null, lastSync: null }
        }
      }
    });
    cy.get('app-sidebar').contains('Integrações').click();
    cy.wait('@getTelegramStatusConnected', { timeout: 10000 });
  };

  it('should show Telegram card in integrations page', () => {
    setupDisconnected();
    cy.get('[data-cy="card-telegram"]', { timeout: 10000 }).should('be.visible');
    cy.contains('Converse com a IA pelo Telegram').should('be.visible');
  });

  it('should open Telegram config modal', () => {
    setupDisconnected();
    cy.get('[data-cy="card-telegram"]').click();
    cy.contains('Configuração do Telegram', { timeout: 10000 }).should('be.visible');
  });

  it('should generate linking code', () => {
    setupDisconnected();
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.intercept('POST', '**/api/telegram/generate-code', {
      statusCode: 200,
      body: { code: 'ABC123', expires_in_seconds: 600 }
    }).as('generateCode');
    
    cy.contains('button', 'Gerar Código de Vinculação').click();
    cy.wait('@generateCode');
    
    cy.contains('ABC123').should('be.visible');
    cy.contains('Código válido por 10 minutos').should('be.visible');
  });

  it('should copy code to clipboard', () => {
    setupDisconnected();
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.intercept('POST', '**/api/telegram/generate-code', {
      statusCode: 200,
      body: { code: 'XYZ789', expires_in_seconds: 600 }
    }).as('generateCode');
    
    cy.contains('button', 'Gerar Código de Vinculação').click();
    cy.wait('@generateCode');
    
    // Mock clipboard API
    cy.window().then((win) => {
      cy.stub(win.navigator.clipboard, 'writeText').resolves();
    });
    
    cy.contains('button', 'Copiar').click();
    cy.contains('Código copiado!').should('be.visible');
  });

  it('should show connected state', () => {
    setupConnected();
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.contains('Conta vinculada com sucesso!').should('be.visible');
    cy.contains('@testuser').should('be.visible');
    cy.contains('button', 'Desvincular Conta').should('be.visible');
  });

  it('should unlink account', () => {
    setupConnected();
    cy.get('[data-cy="card-telegram"]').click();
    
    // Stub window.confirm to auto-confirm
    cy.window().then((win) => {
      cy.stub(win, 'confirm').returns(true);
    });
    
    cy.intercept('POST', '**/api/telegram/unlink', {
      statusCode: 200,
      body: { message: 'Unlinked successfully' }
    }).as('unlink');
    
    cy.intercept('GET', '**/api/telegram/status', {
      statusCode: 200,
      body: { linked: false }
    }).as('getStatusAfterUnlink');
    
    cy.contains('button', 'Desvincular Conta').click();
    cy.wait('@unlink');
    cy.wait('@getStatusAfterUnlink');
    
    cy.contains('button', 'Gerar Código de Vinculação').should('be.visible');
  });

  it('should close modal', () => {
    setupDisconnected();
    cy.get('[data-cy="card-telegram"]').click();
    cy.contains('Configuração do Telegram').should('be.visible');
    
    // Click close button (X)
    cy.get('app-telegram-config button').find('svg').first().click({ force: true });
    cy.contains('Configuração do Telegram').should('not.exist');
  });
});
