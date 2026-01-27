/**
 * Error scenarios for Cypress tests
 */
export const ERROR_MOCKS = {
  unauthorized: {
    statusCode: 401,
    body: { detail: 'Unauthorized' }
  },

  forbidden: {
    statusCode: 403,
    body: { detail: 'Forbidden' }
  },

  notFound: {
    statusCode: 404,
    body: { detail: 'Not found' }
  },

  conflict: {
    statusCode: 409,
    body: { detail: 'Conflict' }
  },

  validationError: {
    statusCode: 422,
    body: {
      detail: [
        { loc: ['body', 'email'], msg: 'Invalid email format' }
      ]
    }
  },

  tooManyRequests: {
    statusCode: 429,
    body: { detail: 'Too many requests' }
  },

  serverError: {
    statusCode: 500,
    body: { detail: 'Internal server error' }
  },

  badGateway: {
    statusCode: 502,
    body: { detail: 'Bad Gateway' }
  },

  serviceUnavailable: {
    statusCode: 503,
    body: { detail: 'Service Unavailable' }
  },

  networkError: {
    forceNetworkError: true
  }
};

/**
 * Factory para criar respostas de erro customizadas
 */
export const createErrorResponse = (
  statusCode: number,
  detail: string,
  extra?: any
) => ({
  statusCode,
  body: {
    detail,
    ...extra
  }
});

/**
 * Factory para criar erros de validação
 */
export const createValidationError = (
  field: string,
  message: string
) => ({
  statusCode: 422,
  body: {
    detail: [
      { loc: ['body', field], msg: message }
    ]
  }
});
