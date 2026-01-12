describe('Mobile Navigation', () => {
    beforeEach(() => {
        // Essential startup intercepts for Dashboard
        cy.intercept('GET', '**/trainer/trainer_profile', { body: { trainer_type: 'atlas' } }).as('trainerProfile');
        cy.intercept('GET', '**/trainer/available_trainers', { body: [{ id: 'atlas', name: 'Atlas' }] }).as('availableTrainers');
        cy.intercept('GET', '**/message/history*', { body: [] }).as('chatHistory');
        cy.intercept('GET', '**/weight/stats*', { body: { latest: null, weight_trend: [] } }).as('getWeightStats');
        cy.intercept('GET', '**/workout/stats', { body: { streak: 0, frequency: [] } }).as('getWorkoutStats');
        cy.intercept('GET', '**/nutrition/stats', { body: { daily_target: 2000, current_macros: {} } }).as('getNutritionStats');
        cy.intercept('GET', '**/user/profile', { body: { email: 'cypress@test.com' } }).as('userProfile');
    });

    const silentLogin = () => {
        cy.visit('/', {
            onBeforeLoad: (win) => {
                win.localStorage.setItem('jwt_token', 'fake-jwt-token');
            }
        });
        cy.get('app-sidebar', { timeout: 10000 }).should('exist');
        cy.get('app-dashboard', { timeout: 10000 }).should('exist');
    };

    it('should show sidebar and hide hamburger on desktop', () => {
        cy.viewport(1280, 720);
        silentLogin();
        
        // Sidebar wrapper should be visible and not translated
        cy.get('[data-cy="sidebar-wrapper"]').should('be.visible');
        
        // Mobile header should be hidden on desktop
        cy.get('[data-cy="mobile-header"]').should('not.be.visible');
    });

    it('should hide sidebar and show hamburger on mobile', () => {
        cy.viewport('iphone-x'); // 375 x 812
        silentLogin();
        
        // Mobile header should be visible
        cy.get('[data-cy="mobile-header"]').should('be.visible');
        
        // Hamburger button should be visible
        cy.get('[data-cy="mobile-menu-btn"]').should('be.visible');
        
        // Sidebar wrapper should be translated off screen
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', '-translate-x-full');
    });

    it('should open sidebar when hamburger is clicked on mobile', () => {
        cy.viewport('iphone-x');
        silentLogin();
        
        // Click hamburger
        cy.get('[data-cy="mobile-menu-btn"]').should('be.visible').click();
        
        // Sidebar wrapper should be moved into view
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', 'translate-x-0');
        
        // Backdrop should be visible
        cy.get('[data-cy="mobile-backdrop"]').should('exist');
    });

    it('should close sidebar when backdrop is clicked', () => {
        cy.viewport('iphone-x');
        silentLogin();
        
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
        silentLogin();
        
        // Open menu
        cy.get('[data-cy="mobile-menu-btn"]').click();
        
        // Click "Meu Perfil" in sidebar
        cy.contains('button', 'Meu Perfil').click({ force: true });
        cy.wait('@userProfile');
        
        // Sidebar should auto close
        cy.get('[data-cy="sidebar-wrapper"]').should('have.class', '-translate-x-full');
        
        // Should have navigated
        cy.get('app-user-profile', { timeout: 10000 }).should('be.visible');
    });
});
