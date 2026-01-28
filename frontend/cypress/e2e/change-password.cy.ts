import { COMMON_MOCKS, ERROR_MOCKS } from '../support/mocks';

/**
 * SKIPPED: Change password component not yet implemented
 * The app uses signals-based navigation (NavigationService), not routes.
 * See src/services/navigation.service.ts for available views.
 */
describe.skip('Change Password Flow', () => {
  beforeEach(() => {
    // Mock user is logged in
    cy.mockLogin();
    // Navigate using NavigationService (not via URL)
    // cy.navigateTo('user-profile'); // When implemented
  });

  it('should successfully change password', () => {
    cy.intercept('POST', '**/user/change-password', { body: { success: true } }).as('changePassword');

    cy.get('input[name="currentPassword"]').type('CurrentPassword123!');
    cy.get('input[name="newPassword"]').type('NewPassword456!');
    cy.get('input[name="confirmPassword"]').type('NewPassword456!');
    cy.get('button').contains('Alterar Senha').click();

    cy.wait('@changePassword');
    cy.contains('Senha alterada com sucesso').should('be.visible');
  });

  it('should validate current password incorrectly', () => {
    cy.intercept('POST', '**/user/change-password', { statusCode: 401, body: { detail: 'Wrong password' } }).as(
      'wrongPassword'
    );

    cy.get('input[name="currentPassword"]').type('WrongPassword!');
    cy.get('input[name="newPassword"]').type('NewPassword456!');
    cy.get('input[name="confirmPassword"]').type('NewPassword456!');
    cy.get('button').contains('Alterar Senha').click();

    cy.wait('@wrongPassword');
    cy.contains('Senha atual incorreta').should('be.visible');
  });

  it('should reject weak new password', () => {
    cy.get('input[name="currentPassword"]').type('CurrentPassword123!');
    cy.get('input[name="newPassword"]').type('weak');
    cy.get('button').contains('Alterar Senha').should('be.disabled');
  });

  it('should validate password confirmation', () => {
    cy.get('input[name="currentPassword"]').type('CurrentPassword123!');
    cy.get('input[name="newPassword"]').type('NewPassword456!');
    cy.get('input[name="confirmPassword"]').type('DifferentPassword!');
    cy.get('button').contains('Alterar Senha').should('be.disabled');
  });

  it('should show loading state during change', () => {
    cy.intercept('POST', '**/user/change-password', { delay: 1000, body: { success: true } }).as('changePasswordSlow');

    cy.get('input[name="currentPassword"]').type('CurrentPassword123!');
    cy.get('input[name="newPassword"]').type('NewPassword456!');
    cy.get('input[name="confirmPassword"]').type('NewPassword456!');
    cy.get('button').contains('Alterar Senha').click();

    cy.get('[data-test="loading-spinner"]').should('be.visible');
    cy.wait('@changePasswordSlow');
  });

  it('should handle server error', () => {
    cy.intercept('POST', '**/user/change-password', ERROR_MOCKS.serverError).as('serverError');

    cy.get('input[name="currentPassword"]').type('CurrentPassword123!');
    cy.get('input[name="newPassword"]').type('NewPassword456!');
    cy.get('input[name="confirmPassword"]').type('NewPassword456!');
    cy.get('button').contains('Alterar Senha').click();

    cy.wait('@serverError');
    cy.contains('Erro ao alterar senha').should('be.visible');
  });

  it('should clear form after success', () => {
    cy.intercept('POST', '**/user/change-password', { body: { success: true } }).as('changePassword');

    cy.get('input[name="currentPassword"]').type('CurrentPassword123!');
    cy.get('input[name="newPassword"]').type('NewPassword456!');
    cy.get('input[name="confirmPassword"]').type('NewPassword456!');
    cy.get('button').contains('Alterar Senha').click();

    cy.wait('@changePassword');

    cy.get('input[name="currentPassword"]').should('have.value', '');
    cy.get('input[name="newPassword"]').should('have.value', '');
  });
});
