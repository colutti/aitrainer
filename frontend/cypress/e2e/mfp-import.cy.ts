Mfp-import|describe('MyFitnessPal Import - E2E', () => {
    beforeEach(() => {
        // mockLogin now handles the default integration checks via setupCommonIntercepts
        cy.mockLogin();
        cy.get('app-sidebar').contains('Integrações').click();
        cy.get('app-integrations').should('be.visible');
    });

    it('should open MFP import modal and show instructions', () => {
        cy.get('[data-cy="card-mfp"]').click();
        cy.contains('h2', 'MyFitnessPal').should('be.visible');
        cy.contains('Como exportar seus dados').should('be.visible');
    });

    it('should successfully upload CSV file', () => {
        cy.get('[data-cy="card-mfp"]').click();
        
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

        // Select file - Using a dummy CSV content
        const csvContent = "Date,Meal,Calories,Fat,Carbohydrates,Protein\n2024-01-01,Breakfast,300,10,30,20";
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from(csvContent),
            fileName: 'my_data.csv',
            mimeType: 'text/csv'
        }, { force: true });

        cy.contains('Arquivo selecionado: my_data.csv').scrollIntoView().should('be.visible');
        
        cy.contains('button', 'Importar Dados').click();
        
        cy.wait('@importCsv');

        cy.contains('Importação Concluída!', { timeout: 10000 }).scrollIntoView().should('be.visible');
        cy.contains('Novos').parent().contains('5');
    });
    
    it('should show error for invalid file type', () => {
        cy.get('[data-cy="card-mfp"]').click();
        
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from('not a csv'),
            fileName: 'document.pdf',
            mimeType: 'application/pdf'
        }, { force: true });

        cy.contains('Por favor, selecione um arquivo .csv').scrollIntoView().should('be.visible');
    });

    it('should handle API error gracefully', () => {
        cy.get('[data-cy="card-mfp"]').click();
        
        cy.intercept('POST', '**/nutrition/import/myfitnesspal', {
            statusCode: 400,
            body: { detail: 'Formato de CSV inválido' }
        }).as('importError');

        const csvContent = "invalid,garbage\ndata";
        cy.get('input[type=file]').selectFile({
            contents: Cypress.Buffer.from(csvContent),
            fileName: 'invalid.csv',
            mimeType: 'text/csv'
        }, { force: true });
        
        cy.contains('button', 'Importar Dados').click();
        cy.wait('@importError');

        cy.contains('Formato de CSV inválido').scrollIntoView().should('be.visible');
    });
});
