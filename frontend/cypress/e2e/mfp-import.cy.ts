describe('MyFitnessPal Import - E2E', () => {
    beforeEach(() => {
        cy.mockLogin({
            intercepts: {
                 '**/integrations/hevy/status': { 
                    statusCode: 200,
                    body: { enabled: false, has_key: false, api_key_masked: null, last_sync: null }
                }
            }
        });
        cy.get('app-sidebar').contains('Integrações').click();
    });

    it('should open MFP import modal and show instructions', () => {
        cy.contains('MyFitnessPal').closest('app-integration-card').click();
        cy.contains('h2', 'MyFitnessPal').should('be.visible');
        cy.contains('Como exportar seus dados').should('be.visible');
        cy.contains('Via Website').should('be.visible');
    });

    it('should successfully upload CSV file', () => {
        cy.contains('MyFitnessPal').closest('app-integration-card').click();
        
        // Mock Import API
        cy.intercept('POST', '**/nutrition/import/myfitnesspal', {
            statusCode: 200,
            body: { 
                created: 5, 
                updated: 2, 
                errors: 0, 
                total_days: 7, 
                error_messages: [] 
            }
        }).as('importCsv');

        // Select file
        const csvContent = "Data,Refeição,Calorias,Gorduras (g),Carboidratos (g),Proteínas (g)\n2024-01-01,Café,300,10,30,20";
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from(csvContent),
            fileName: 'my_data.csv',
            mimeType: 'text/csv'
        }, { force: true });

        cy.contains('Arquivo selecionado: my_data.csv').should('be.visible');
        
        cy.contains('button', 'Importar Dados').click();
        
        cy.wait('@importCsv');

        cy.contains('Importação Concluída!').should('be.visible');
        // Check grid stats
        cy.contains('Novos').parent().contains('5');
        cy.contains('Atualizados').parent().contains('2');
        cy.contains('Total de dias processados').parent().contains('7');
    });
    
    it('should show error for invalid file type', () => {
        cy.contains('MyFitnessPal').closest('app-integration-card').click();
        
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from('some text'),
            fileName: 'bad.txt',
            mimeType: 'text/plain'
        }, { force: true });

        cy.contains('Por favor, selecione um arquivo .csv').should('be.visible');
        cy.contains('button', 'Importar Dados').should('be.disabled');
    });

     it('should handle API error gracefully', () => {
        cy.contains('MyFitnessPal').closest('app-integration-card').click();
        
        cy.intercept('POST', '**/nutrition/import/myfitnesspal', {
            statusCode: 400,
            body: { detail: 'CSV Validation Error' }
        }).as('importCsvError');

        const csvContent = "Invalid content";
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from(csvContent),
            fileName: 'my_data.csv',
            mimeType: 'text/csv'
        }, { force: true });
        
        cy.contains('button', 'Importar Dados').click();
        cy.wait('@importCsvError');
        
        cy.contains('CSV Validation Error').should('be.visible');
        // Button should be re-enabled or UI reset to allow retry (in current logic, it goes back to setup)
        cy.contains('button', 'Importar Dados').should('be.visible');
    });
});
