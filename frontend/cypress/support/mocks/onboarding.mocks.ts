/**
 * Onboarding-related mocks for Cypress tests
 */
export const ONBOARDING_MOCKS = {
  validInvite: {
    statusCode: 200,
    body: {
      valid: true,
      email: 'newuser@test.com'
    }
  },

  invalidInvite: {
    statusCode: 404,
    body: {
      detail: 'Código de convite inválido ou expirado'
    }
  },

  expiredInvite: {
    statusCode: 410,
    body: {
      detail: 'Código de convite expirado'
    }
  },

  onboardSuccess: {
    statusCode: 200,
    body: {
      token: 'new_user_jwt_token_here',
      email: 'newuser@test.com'
    }
  },

  onboardValidationError: {
    statusCode: 422,
    body: {
      detail: [
        { loc: ['body', 'password'], msg: 'Password must be at least 8 characters' }
      ]
    }
  },

  passwordMismatch: {
    statusCode: 422,
    body: {
      detail: [
        { loc: ['body', 'confirmPassword'], msg: 'Passwords do not match' }
      ]
    }
  }
};
