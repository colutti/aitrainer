describe('Zepp Life Import - E2E', () => {
    beforeEach(() => {
        cy.mockLogin();
        // Mock Hevy/Telegram endpoints to prevent 404s if any
        cy.intercept('GET', '**/integrations/hevy/status', { enabled: false, hasKey: false }).as('hevyStatus');
        cy.intercept('GET', '**/telegram/status', { linked: false }).as('telegramStatus');
        
        cy.get('app-sidebar').contains('Integrações').click();
        cy.get('app-integrations').should('be.visible');
    });

    it('should open Zepp Life import modal', () => {
        cy.get('[data-cy="card-zepp-life"]').click();
        cy.contains('h2', 'Importar Zepp Life').should('be.visible');
        cy.contains('Exporte seus dados do aplicativo Zepp Life').should('be.visible');
    });

    it('should successfully upload CSV file', () => {
        cy.get('[data-cy="card-zepp-life"]').click();
        
        // Mock Import API
        cy.intercept('POST', '**/weight/import/zepp-life', {
            statusCode: 200,
            body: { 
                created: 10, 
                updated: 0, 
                errors: 0, 
                total_days: 10, 
                error_messages: [] 
            }
        }).as('importCsv');

        // Select file - Using a dummy CSV content
        const csvContent = "time,weight,fatRate\n2025-01-01,80,20";
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from(csvContent),
            fileName: 'BODY.csv',
            mimeType: 'text/csv'
        }, { force: true });
        
        cy.contains('BODY.csv').should('be.visible');
        
        cy.contains('button', 'Importar Dados').click();
        
        cy.wait('@importCsv');

        cy.contains('Importação Concluída').should('be.visible');
        cy.contains('Criados').parent().contains('+10');
    });
    
    it('should show error for invalid file type', () => {
        cy.get('[data-cy="card-zepp-life"]').click();
        
        cy.get('app-zepp-life-import input[type=file]').selectFile({
            contents: Cypress.Buffer.from('not a csv'),
            fileName: 'image.png',
            mimeType: 'image/png'
        }, { force: true });

        cy.contains('Por favor selecione um arquivo CSV').should('be.visible');
    });

    it('should handle API error gracefully', () => {
        cy.get('[data-cy="card-zepp-life"]').click();
        
        cy.intercept('POST', '**/weight/import/zepp-life', {
            statusCode: 400,
            body: { detail: 'CSV Inválido' }
        }).as('importError');

        const csvContent = "invalid,garbage\ndata";
        cy.get('app-zepp-life-import input[type=file]').selectFile({
            contents: Cypress.Buffer.from(csvContent),
            fileName: 'invalid.csv',
            mimeType: 'text/csv'
        }, { force: true });
        
        cy.contains('button', 'Importar Dados').click();
        cy.wait('@importError');

        cy.contains('CSV Inválido').should('be.visible');
    });
});
