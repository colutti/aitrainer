describe('Navigation Flow', () => {
    beforeEach(() => {
        // Use 100% mocked login
        cy.mockLogin({
            intercepts: {
                '**/trainer/trainer_profile': { body: { trainer_type: 'sofia' }, alias: 'trainerProfile' },
                '**/user/profile': {
                    statusCode: 200,
                    body: {
                        email: 'cypress@test.com',
                        gender: 'Masculino',
                        age: 30,
                        weight: 80,
                        height: 180,
                        goal: 'Ganhar massa'
                    },
                    alias: 'userProfile'
                }
            }
        });
    });

    it('should navigate from Dashboard to User Profile', () => {
        // Start on dashboard (default after login)
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');

        // Navigate to user profile
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');

        // Verify correct view is displayed
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');
        cy.get('app-dashboard').should('not.exist');
    });

    it('should navigate from User Profile to Trainer Settings', () => {
        // Go to user profile first
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');

        // Navigate to trainer settings
        cy.contains('button', 'Ajustes do Trainer').click({ force: true });
        cy.wait('@trainerProfile');

        // Verify correct view is displayed
        cy.get('app-trainer-settings', { timeout: 10000 }).should('be.visible');
        cy.get('app-user-profile').should('not.exist');
    });

    it('should navigate from Trainer Settings back to Dashboard', () => {
        // Go to trainer settings first
        cy.contains('button', 'Ajustes do Trainer').click({ force: true });
        cy.wait('@trainerProfile');
        cy.get('app-trainer-settings', { timeout: 10000 }).should('be.visible');

        // Navigate back to dashboard
        cy.contains('button', 'Home').click({ force: true });

        // Verify correct view is displayed
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
        cy.get('app-trainer-settings').should('not.exist');
    });

    it('should highlight the active navigation button', () => {
        // Wait for dashboard to load
        cy.get('app-dashboard', { timeout: 10000 }).should('be.visible');
        
        // Home button should be active initially
        cy.contains('button', 'Home')
            .should('have.class', 'bg-primary');

        // Navigate to user profile
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');

        // User profile button should now be active
        cy.contains('button', 'Meu Perfil')
            .should('have.class', 'bg-primary');

        // Home button should no longer be active
        cy.contains('button', 'Home')
            .should('not.have.class', 'bg-primary');
    });

    it('should allow scrolling to logout button when user is admin', () => {
        cy.viewport(1280, 500); // Very small height to force overflow
    
        // We need to re-login as admin for this test logic, or mock the specific state
        // Since beforeEach logs in with default mock, we override it here
        cy.mockLogin({
          intercepts: {
            'GET **/user/me': {
                 statusCode: 200,
                 body: { email: 'admin@test.com', role: 'admin' },
                 alias: 'userInfo'
            }
          }
        });
    
        cy.get('app-sidebar').should('be.visible');
        
        // Check that admin menu items are present
        cy.contains('SPAN', 'Dashboard').should('exist'); // Admin dashboard text inside span
        
        // Sair button should exist
        cy.contains('button', 'Sair').should('exist');
    
        // Verify nav has overflow property and can scroll
        cy.get('nav')
          .should('have.css', 'overflow-y', 'auto')
          .scrollTo('bottom');
          
        cy.contains('button', 'Sair').should('be.visible');
    });
});
