describe('Mobile Navigation', () => {
    beforeEach(() => {
        // 100% Mocked Login with user profile intercept for navigation tests
        cy.mockLogin({
            intercepts: {
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

    it('should show sidebar and hide hamburger on desktop', () => {
        cy.viewport(1280, 720);
        
        // Sidebar wrapper should be visible and not translated
        cy.get('[data-cy="sidebar-wrapper"]').should('be.visible');
        
        // Mobile header should be hidden on desktop
        cy.get('[data-cy="mobile-header"]').should('not.be.visible');
    });

    it('should hide sidebar and show hamburger on mobile', () => {
        cy.viewport('iphone-x'); // 375 x 812
        
        // Mobile header should be visible
        cy.get('[data-cy="mobile-header"]').should('be.visible');
        
        // Hamburger button should be visible
        cy.get('[data-cy="mobile-menu-btn"]').should('be.visible');
        
        // Sidebar wrapper should be translated off screen
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', '-translate-x-full');
    });

    it('should open sidebar when hamburger is clicked on mobile', () => {
        cy.viewport('iphone-x');
        
        // Click hamburger
        cy.get('[data-cy="mobile-menu-btn"]').should('be.visible').click();
        
        // Sidebar wrapper should be moved into view
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', 'translate-x-0');
        
        // Backdrop should be visible
        cy.get('[data-cy="mobile-backdrop"]').should('exist');
    });

    it('should close sidebar when backdrop is clicked', () => {
        cy.viewport('iphone-x');
        
        // Open menu
        cy.get('[data-cy="mobile-menu-btn"]').click();
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', 'translate-x-0');
        
        // Click backdrop
        cy.get('[data-cy="mobile-backdrop"]').click({ force: true });
        
        // Sidebar should be hidden again
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', '-translate-x-full');
    });

    it('should auto-close sidebar when navigating on mobile', () => {
        cy.viewport('iphone-x');
        
        // Open menu
        cy.get('[data-cy="mobile-menu-btn"]').click();
        
        // Click "Coach" in sidebar
        cy.contains('button', 'Coach').click({ force: true });
        
        // Sidebar should auto close
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', '-translate-x-full');
        
        // Should have navigated to chat view (which is coach)
        cy.get('app-chat', { timeout: 10000 }).should('be.visible');
    });
});
