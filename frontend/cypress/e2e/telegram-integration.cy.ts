Telegram-integration|describe('Telegram Integration', () => {
  const setupTest = (linked: boolean = false) => {
    cy.mockLogin({
      intercepts: {
        '**/api/telegram/status': {
          statusCode: 200,
          body: linked ? { 
            linked: true, 
            telegram_username: '@testuser',
            linked_at: '2026-01-19T20:00:00Z'
          } : { linked: false }
        }
      }
    });
    cy.get('app-sidebar').contains('Integrações').click();
    cy.get('app-integrations').should('be.visible');
  };

  it('should show Telegram card in integrations page', () => {
    setupTest(false);
    cy.get('[data-cy="card-telegram"]').should('be.visible');
    cy.contains('Converse com a IA pelo Telegram').should('be.visible');
  });

  it('should open Telegram config modal', () => {
    setupTest(false);
    cy.get('[data-cy="card-telegram"]').click();
    cy.contains('Configuração do Telegram').should('be.visible');
  });

  it('should generate linking code', () => {
    setupTest(false);
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.intercept('POST', '**/api/telegram/generate-code', {
      statusCode: 200,
      body: { code: 'ABC123', expires_in_seconds: 600 }
    }).as('generateCode');
    
    cy.contains('button', 'Gerar Código').click();
    cy.wait('@generateCode');
    
    cy.contains('ABC123').should('be.visible');
    cy.contains('Código gerado! Válido por 10 minutos.').should('be.visible');
  });

  it('should copy code to clipboard', () => {
    setupTest(false);
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.intercept('POST', '**/api/telegram/generate-code', {
      statusCode: 200,
      body: { code: 'XYZ789', expires_in_seconds: 600 }
    }).as('generateCode');
    
    cy.contains('button', 'Gerar Código').click();
    cy.wait('@generateCode');
    
    // Mock clipboard API for headless reliability
    cy.window().then((win) => {
      if (!win.navigator.clipboard) {
        (win.navigator as any).clipboard = { writeText: cy.stub().resolves() };
      } else {
        cy.stub(win.navigator.clipboard, 'writeText').resolves();
      }
    });
    
    cy.contains('button', 'Copiar').click({ force: true });
    cy.contains('Código copiado!').should('be.visible');
  });

  it('should show connected state', () => {
    setupTest(true);
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.contains('Conta vinculada com sucesso!').should('be.visible');
    cy.contains('@testuser').should('be.visible');
    cy.contains('button', 'Desvincular Conta').should('be.visible');
  });

  it('should unlink account', () => {
    setupTest(true);
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.on('window:confirm', () => true);
    
    cy.intercept('POST', '**/api/telegram/unlink', {
      statusCode: 200,
      body: { message: 'Unlinked successfully' }
    }).as('unlink');
    
    // Status re-fetch after unlink should return disconnected
    cy.intercept('GET', '**/api/telegram/status', {
      statusCode: 200,
      body: { linked: false }
    }).as('getStatusAfterUnlink');
    
    cy.contains('button', 'Desvincular Conta').click();
    cy.wait('@unlink');
    cy.wait('@getStatusAfterUnlink');
    
    cy.contains('button', 'Gerar Código').should('be.visible');
  });

  it('should close modal', () => {
    setupTest(false);
    cy.get('[data-cy="card-telegram"]').click();
    
    cy.get('app-telegram-config button').find('svg').first().click({ force: true });
    cy.contains('Configuração do Telegram').should('not.exist');
  });
});
