import { ONBOARDING_MOCKS, ERROR_MOCKS } from '../support/mocks';

describe('Onboarding Flow', () => {
  beforeEach(() => {
    cy.intercept('POST', '**/user/validate_invite', ONBOARDING_MOCKS.validInvite).as('validateInvite');
    cy.intercept('POST', '**/user/onboard', ONBOARDING_MOCKS.onboardSuccess).as('onboard');
    cy.visit('/onboarding');
  });

  it('should complete onboarding with valid invite code', () => {
    cy.get('input[name="inviteCode"]').type('VALID_CODE_123');
    cy.get('button').contains('Validar').click();
    cy.wait('@validateInvite');

    cy.get('input[name="password"]').type('SecurePassword123!');
    cy.get('input[name="confirmPassword"]').type('SecurePassword123!');
    cy.get('button').contains('Criar Conta').click();
    cy.wait('@onboard');

    cy.url().should('include', '/dashboard');
  });

  it('should show error for invalid invite code', () => {
    cy.intercept('POST', '**/user/validate_invite', ONBOARDING_MOCKS.invalidInvite).as('invalidInvite');

    cy.get('input[name="inviteCode"]').type('INVALID_CODE');
    cy.get('button').contains('Validar').click();
    cy.wait('@invalidInvite');

    cy.contains('Código de convite inválido').should('be.visible');
  });

  it('should show error for expired invite', () => {
    cy.intercept('POST', '**/user/validate_invite', ONBOARDING_MOCKS.expiredInvite).as('expiredInvite');

    cy.get('input[name="inviteCode"]').type('EXPIRED_CODE');
    cy.get('button').contains('Validar').click();
    cy.wait('@expiredInvite');

    cy.contains('Código expirado').should('be.visible');
  });

  it('should validate password mismatch', () => {
    cy.get('input[name="inviteCode"]').type('VALID_CODE_123');
    cy.get('button').contains('Validar').click();
    cy.wait('@validateInvite');

    cy.get('input[name="password"]').type('Password123!');
    cy.get('input[name="confirmPassword"]').type('DifferentPassword!');
    cy.get('button').contains('Criar Conta').click();

    cy.contains('Senhas não correspondem').should('be.visible');
  });

  it('should validate password requirements', () => {
    cy.get('input[name="inviteCode"]').type('VALID_CODE_123');
    cy.get('button').contains('Validar').click();
    cy.wait('@validateInvite');

    cy.get('input[name="password"]').type('weak');
    cy.get('button').contains('Criar Conta').should('be.disabled');
  });

  it('should show loading state during validation', () => {
    cy.get('input[name="inviteCode"]').type('VALID_CODE_123');
    cy.get('button').contains('Validar').click();

    cy.get('[data-test="loading-spinner"]').should('be.visible');
    cy.wait('@validateInvite');
  });

  it('should disable form during submission', () => {
    cy.get('input[name="inviteCode"]').type('VALID_CODE_123');
    cy.get('button').contains('Validar').click();
    cy.wait('@validateInvite');

    cy.get('input[name="password"]').type('SecurePassword123!');
    cy.get('input[name="confirmPassword"]').type('SecurePassword123!');
    cy.get('button').contains('Criar Conta').click();

    cy.get('input[name="password"]').should('be.disabled');
    cy.wait('@onboard');
  });

  it('should handle validation error from server', () => {
    cy.intercept('POST', '**/user/validate_invite', ONBOARDING_MOCKS.onboardValidationError).as('validationError');

    cy.get('input[name="inviteCode"]').type('CODE');
    cy.get('button').contains('Validar').click();
    cy.wait('@validationError');

    cy.contains('erro de validação').should('be.visible');
  });
});
