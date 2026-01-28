
import { setupCommonIntercepts } from '../support/intercepts';

describe('Admin Users Management', () => {
    const adminUser = { email: 'admin@test.com', role: 'admin' };
    const mockUsers = {
        users: [
            { email: 'user1@test.com', role: 'user', age: 25, goal_type: 'lose_weight' },
            { email: 'admin@test.com', role: 'admin', age: 30, goal_type: 'maintain' },
            { email: 'otheradmin@test.com', role: 'admin', age: 35, goal_type: 'gain_muscle' }
        ],
        total_pages: 1
    };
    const userDetails = {
        email: 'user1@test.com',
        role: 'user',
        profile: { name: 'User One', age: 25, height: 180, weight: 75 }
    };

    beforeEach(() => {
        cy.window().then(win => win.localStorage.clear());
        setupCommonIntercepts();
        
        cy.intercept('GET', '**/user/me', { body: adminUser }).as('userMe');
        cy.intercept('GET', '**/user/profile', { body: adminUser }).as('userProfile');
        cy.intercept('GET', '**/admin/users/list*', { body: mockUsers }).as('getUsers');
        cy.intercept('GET', '**/admin/users/*/details', { body: userDetails }).as('getUserDetails');
        cy.intercept('DELETE', '**/admin/users/user1@test.com', { statusCode: 200, body: { message: 'Deleted' } }).as('deleteUser');
        
        const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImN5cHJlc3NfdXNlckB0ZXN0LmNvbSIsImV4cCI6OTk5OTk5OTk5OX0.fake';
        cy.visit('/', {
            onBeforeLoad: (win) => {
                win.localStorage.setItem('jwt_token', mockToken);
            }
        });
        
        cy.get('app-sidebar').should('be.visible');
        cy.get('button[data-cy="nav-admin-users"]').click({ force: true });
    });

    it('should display the list of users', () => {
        cy.wait('@getUsers');
        cy.get('table').should('be.visible');
        cy.contains('td', 'user1@test.com').should('be.visible');
    });

    it('should view user details in a modal', () => {
        cy.wait('@getUsers');

        cy.contains('tr', 'user1@test.com')
            .find('button').contains('Ver')
            .click();

        cy.wait('@getUserDetails');

        // Check for modal presence
        cy.contains('h2', 'Detalhes do Usuário').should('be.visible');
        cy.get('pre').should('include.text', 'user1@test.com');

        // Close modal - find the button with X icon within the modal header
        cy.contains('h2', 'Detalhes do Usuário')
            .parent()
            .find('button svg')
            .parent()
            .click();

        cy.contains('h2', 'Detalhes do Usuário').should('not.exist');
    });

    it('should handle delete user with confirmation', () => {
        cy.wait('@getUsers');
        
        const confirmStub = cy.stub().returns(true);
        cy.on('window:confirm', confirmStub);
        
        // We use NotificationService success toast, so check for that
        cy.contains('tr', 'user1@test.com')
            .find('button').contains('Deletar')
            .click();
            
        cy.wait('@deleteUser');
        
        // Assert NotificationService toast (it's in the DOM usually)
        cy.contains('Usuário deletado com sucesso').should('be.visible');
    });

    it('should visually disable delete for admins', () => {
        cy.wait('@getUsers');
        
        // Find the row for otheradmin
        cy.contains('tr', 'otheradmin@test.com').within(() => {
            // Should NOT have a "Deletar" button, but a span or text
            cy.get('button').contains('Deletar').should('not.exist');
            cy.contains('Deletar').should('have.class', 'cursor-not-allowed');
        });
    });
});
