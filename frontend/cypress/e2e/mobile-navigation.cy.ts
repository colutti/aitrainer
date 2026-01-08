describe('Mobile Navigation', () => {
    beforeEach(() => {
        // Login before each test
        cy.login('cypress_user@test.com', 'Ce568f36-8bdc-47f6-8a63-ebbfd4bf4661');
    });

    it('should show sidebar and hide hamburger on desktop', () => {
        cy.viewport(1280, 720);
        
        // Sidebar should be visible
        cy.get('app-sidebar').should('be.visible');
        
        // Hamburger button should be hidden on desktop
        // It exists in DOM but hidden by CSS (md:hidden)
        cy.get('[data-cy="mobile-header"]').should('not.be.visible');
    });

    it('should hide sidebar and show hamburger on mobile', () => {
        cy.viewport('iphone-x'); // 375 x 812
        
        // Mobile header should be visible
        cy.get('[data-cy="mobile-header"]').should('be.visible');
        
        // Hamburger button should be visible
        cy.get('[data-cy="mobile-menu-btn"]').should('be.visible');
        
        // Sidebar should be hidden initially (translated off screen)
        // With overflow hidden on parent, it should be not visible.
        cy.get('app-sidebar').should('not.be.visible');
    });

    it('should open sidebar when hamburger is clicked on mobile', () => {
        cy.viewport('iphone-x');
        
        // Click hamburger
        cy.get('[data-cy="mobile-menu-btn"]').click();
        
        // Sidebar should be visible
        cy.get('app-sidebar').should('be.visible');
        
        // Backdrop should be visible (partially covered by sidebar, so strict visibility might fail)
        cy.get('[data-cy="mobile-backdrop"]').should('exist');
    });

    it('should close sidebar when backdrop is clicked', () => {
        cy.viewport('iphone-x');
        
        // Open menu
        cy.get('[data-cy="mobile-menu-btn"]').click();
        cy.get('app-sidebar').should('be.visible');
        
        // Click backdrop
        cy.get('[data-cy="mobile-backdrop"]').click({ force: true });
        
        // Sidebar should be hidden again
        cy.get('app-sidebar').should('not.be.visible');
    });

    it('should auto-close sidebar when navigating on mobile', () => {
        cy.viewport('iphone-x');
        
        // Open menu
        cy.get('[data-cy="mobile-menu-btn"]').click();
        
        // Verify we are on chat initially
        cy.get('app-chat').should('be.visible');
        
        // Click "Meu Perfil" in sidebar
        cy.get('app-sidebar button').contains('Meu Perfil').click();
        
        // Sidebar should auto close
        cy.get('app-sidebar').should('not.be.visible');
        
        // Should have navigated
        cy.get('app-user-profile').should('be.visible');
    });
});
