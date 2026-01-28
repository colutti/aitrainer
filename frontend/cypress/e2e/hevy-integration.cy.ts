Hevy-integration|describe('Hevy Integration - Unit E2E Tests', () => {
    // Dynamic State container to simulate backend state changes
    const state = {
        hevyConnected: false,
        hevyApiKey: null as string | null,
        hevyLastSync: null as string | null,
        workoutCount: 0
    };

    const resetState = () => {
        state.hevyConnected = false;
        state.hevyApiKey = null;
        state.hevyLastSync = null;
        state.workoutCount = 0;
    };

    // Helper to setup mock login with dynamic Hevy intercepts
    const setupTest = (initialState: Partial<typeof state> = {}) => {
        resetState();
        Object.assign(state, initialState);

        cy.mockLogin({
            intercepts: {
                // Hevy Status - Dynamic
                'GET **/integrations/hevy/status': (req) => {
                    req.reply({
                        statusCode: 200,
                        body: {
                            enabled: state.hevyConnected,
                            has_key: !!state.hevyApiKey,
                            api_key_masked: state.hevyApiKey ? '****' + state.hevyApiKey.slice(-4) : null,
                            last_sync: state.hevyLastSync
                        }
                    });
                },
                // Hevy Count
                'GET **/integrations/hevy/count': (req) => {
                    req.reply({ statusCode: 200, body: { count: state.workoutCount } });
                },
                // Hevy Webhook Config
                'GET **/integrations/hevy/webhook/config': {
                    statusCode: 200,
                    body: { has_webhook: false }
                },
                // Validate Key
                'POST **/integrations/hevy/validate': {
                    statusCode: 200,
                    body: { valid: true, count: 20 } 
                },
                // Save Config - Updates local 'state' variable
                'POST **/integrations/hevy/config': (req) => {
                    const body = req.body;
                    if (body.enabled === false) {
                         state.hevyConnected = false;
                         state.hevyApiKey = null;
                    } else {
                         state.hevyConnected = true;
                         if (body.api_key) state.hevyApiKey = body.api_key;
                         state.workoutCount = 20; // Simulated
                    }
                    req.reply({ statusCode: 200, body: { message: 'Saved' } });
                },
                // Import
                'POST **/integrations/hevy/import': {
                    statusCode: 200,
                    body: { imported: 5, skipped: 2, failed: 0 }
                }
            }
        });
        
        // Navigation to Integrations
        cy.get('app-sidebar').contains('Integrações').click();
        
        // Use the alias created by mockLogin logic (it aliased 'GET **/integrations/hevy/status' as whatever we named it)
        // Actually, our mockLogin doesn't automatically alias if it's a function handler unless we pass an object.
        // So let's re-alias here for clarity, but this time we match the EXACT same handler.
    };

    it('should show "Conectar" card when disconnected initially', () => {
        setupTest({ hevyConnected: false, hevyApiKey: null });
        
        cy.get('[data-cy="card-hevy"]').within(() => {
            cy.contains('Conectar').should('be.visible');
        });
    });

    it('should transition to "Ativo" after successful connection', () => {
        setupTest({ hevyConnected: false, hevyApiKey: null });

        cy.get('[data-cy="card-hevy"]').click();
        
        // Type key and connect
        cy.get('input[placeholder*="Cole sua chave aqui"]').should('be.visible').type('xxxx-yyyy-4444');
        cy.contains('button', 'Conectar').click();

        // Check success message in modal
        cy.contains('Conectado com sucesso!', { timeout: 15000 }).should('be.visible');
        
        // Close modal
        cy.get('app-hevy-config button').find('svg').first().click({force: true});
        
        // Verify card visual state in the integrations list
        cy.contains('Ativo').should('be.visible');
    });

    it('should successfully run import and show results', () => {
        // Start connected
        setupTest({ 
            hevyConnected: true, 
            hevyApiKey: 'xxxx-yyyy-IMPT',
            hevyLastSync: '2026-01-01T10:00:00Z',
            workoutCount: 10
        });

        cy.get('[data-cy="card-hevy"]').click();
        
        cy.contains('Conectado').should('be.visible');
        cy.contains('Sincronizar Treinos').should('be.visible');

        // Click import button
        cy.contains('button', 'Importar Treinos do Hevy').should('exist').click({ force: true });
        
        // Wait for results
        cy.contains('5 treinos importados com sucesso!', { timeout: 15000 }).should('be.visible');
    });

    it('should successfully disconnect using the multi-step confirm view', () => {
        // Start connected
        setupTest({ 
            hevyConnected: true, 
            hevyApiKey: 'xxxx-yyyy-DISC'
        });
        
        cy.get('[data-cy="card-hevy"]').click();

        cy.contains('button', 'Desconectar').should('exist').click({ force: true });
        cy.contains('h3', 'Desconectar Hevy?').should('be.visible');

        cy.contains('button', 'Sim, desconectar').click({ force: true });

        // UI Should transition back to setup view inside modal
        cy.contains('button', 'Conectar', { timeout: 15000 }).should('be.visible');
        
        // Close modal
        cy.get('app-hevy-config button').find('svg').first().click({force: true});
        
        // Verify card is back to disconnected state
        cy.contains('Conectar').should('be.visible');
    });
});
