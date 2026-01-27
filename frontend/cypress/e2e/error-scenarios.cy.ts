import { ERROR_MOCKS, createErrorResponse } from '../support/mocks/error.mocks';

/**
 * Error Scenarios - Testa tratamento de erros para endpoints críticos
 *
 * Cobertura:
 * - 401 Unauthorized
 * - 403 Forbidden
 * - 404 Not Found
 * - 422 Validation Error
 * - 500 Server Error
 * - 502 Bad Gateway
 * - 503 Service Unavailable
 * - Network errors (forceNetworkError)
 */

describe('Error Scenarios - Critical Endpoints', () => {
  // ==================== 401 UNAUTHORIZED ====================
  describe('401 Unauthorized Errors', () => {
    it('should handle 401 on user profile endpoint', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/user/profile', ERROR_MOCKS.unauthorized).as('unauthorizedProfile');

      cy.visit('/profile');
      cy.wait('@unauthorizedProfile');

      // Should show error or redirect to login
      cy.contains('Não autorizado|Faça login').should('be.visible');
    });

    it('should handle 401 on stats endpoint', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/workout/stats', ERROR_MOCKS.unauthorized).as('unauthorizedStats');

      cy.visit('/dashboard');
      cy.wait('@unauthorizedStats');

      cy.contains('Erro ao carregar|sessão expirou').should('be.visible');
    });

    it('should handle 401 on message endpoint', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/message/message', ERROR_MOCKS.unauthorized).as('unauthorizedMessage');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test message');
      cy.get('button').contains('Enviar').click();
      cy.wait('@unauthorizedMessage');

      cy.contains('Não autorizado|sessão expirou').should('be.visible');
    });
  });

  // ==================== 403 FORBIDDEN ====================
  describe('403 Forbidden Errors', () => {
    it('should handle 403 on admin endpoint', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/admin/**', ERROR_MOCKS.forbidden).as('forbiddenAdmin');

      cy.visit('/admin');
      cy.wait('@forbiddenAdmin');

      cy.contains('Acesso negado|não tem permissão').should('be.visible');
    });

    it('should handle 403 on update user endpoint', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/user/update', ERROR_MOCKS.forbidden).as('forbiddenUpdate');

      cy.visit('/settings');
      cy.get('button').contains('Salvar').click();
      cy.wait('@forbiddenUpdate');

      cy.contains('Acesso negado|permissão insuficiente').should('be.visible');
    });
  });

  // ==================== 404 NOT FOUND ====================
  describe('404 Not Found Errors', () => {
    it('should handle 404 on resource not found', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/workout/123456', ERROR_MOCKS.notFound).as('notFound');

      cy.visit('/workouts/123456');
      cy.wait('@notFound');

      cy.contains('Não encontrado|não existe').should('be.visible');
    });

    it('should handle 404 on nutrition data endpoint', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/nutrition/**', ERROR_MOCKS.notFound).as('nutritionNotFound');

      cy.visit('/nutrition/log');
      cy.wait('@nutritionNotFound');

      cy.contains('Não encontrado|não há dados').should('be.visible');
    });
  });

  // ==================== 422 VALIDATION ERROR ====================
  describe('422 Validation Errors', () => {
    it('should handle validation error on form submission', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/nutrition/log', {
        statusCode: 422,
        body: {
          detail: [
            { loc: ['body', 'calories'], msg: 'Deve ser um número positivo' }
          ]
        }
      }).as('validationError');

      cy.visit('/nutrition/log');
      cy.get('input[name="calories"]').type('-100');
      cy.get('button').contains('Registrar').click();
      cy.wait('@validationError');

      cy.contains('Deve ser um número positivo|validação').should('be.visible');
    });

    it('should handle validation error on password change', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/user/change-password', {
        statusCode: 422,
        body: {
          detail: [
            { loc: ['body', 'newPassword'], msg: 'Senha muito fraca' }
          ]
        }
      }).as('passwordValidationError');

      cy.visit('/settings/security');
      cy.get('input[name="currentPassword"]').type('Current123!');
      cy.get('input[name="newPassword"]').type('weak');
      cy.get('input[name="confirmPassword"]').type('weak');
      cy.get('button').contains('Alterar Senha').click();
      cy.wait('@passwordValidationError');

      cy.contains('Senha muito fraca|validação').should('be.visible');
    });

    it('should handle multiple validation errors', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/workout', {
        statusCode: 422,
        body: {
          detail: [
            { loc: ['body', 'duration'], msg: 'Duração inválida' },
            { loc: ['body', 'exercises'], msg: 'Adicione pelo menos um exercício' }
          ]
        }
      }).as('multipleValidationErrors');

      cy.visit('/workouts/new');
      cy.get('button').contains('Salvar Treino').click();
      cy.wait('@multipleValidationErrors');

      cy.contains('Duração inválida').should('be.visible');
    });
  });

  // ==================== 500 SERVER ERROR ====================
  describe('500 Server Errors', () => {
    it('should handle 500 on message endpoint', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/message/message', ERROR_MOCKS.serverError).as('serverError');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test message');
      cy.get('button').contains('Enviar').click();
      cy.wait('@serverError');

      cy.contains('Erro ao enviar mensagem|servidor').should('be.visible');
    });

    it('should handle 500 on stats endpoint', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/workout/stats', ERROR_MOCKS.serverError).as('statsError');

      cy.visit('/dashboard');
      cy.wait('@statsError');

      cy.contains('Erro ao carregar|servidor').should('be.visible');
    });

    it('should handle 500 on nutrition stats endpoint', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/nutrition/stats', ERROR_MOCKS.serverError).as('nutritionStatsError');

      cy.visit('/nutrition');
      cy.wait('@nutritionStatsError');

      cy.contains('Erro ao carregar|servidor').should('be.visible');
    });

    it('should handle 500 on weight endpoint', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/weight', ERROR_MOCKS.serverError).as('weightError');

      cy.visit('/body-composition');
      cy.get('input[name="weight"]').type('75.5');
      cy.get('button').contains('Salvar').click();
      cy.wait('@weightError');

      cy.contains('Erro ao salvar|servidor').should('be.visible');
    });
  });

  // ==================== 429 TOO MANY REQUESTS ====================
  describe('429 Rate Limit Errors', () => {
    it('should handle 429 rate limit on message endpoint', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/message/message', ERROR_MOCKS.tooManyRequests).as('rateLimited');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test message');
      cy.get('button').contains('Enviar').click();
      cy.wait('@rateLimited');

      cy.contains('muitas requisições|tente novamente|espere').should('be.visible');
    });

    it('should disable form on rate limit', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/nutrition/log', ERROR_MOCKS.tooManyRequests).as('rateLimited');

      cy.visit('/nutrition/log');
      cy.get('input[name="calories"]').type('2000');
      cy.get('button').contains('Registrar').click();
      cy.wait('@rateLimited');

      // Form should remain disabled or show retry timer
      cy.get('[data-test="rate-limit-message"]').should('be.visible');
    });
  });

  // ==================== 502 BAD GATEWAY ====================
  describe('502 Bad Gateway Errors', () => {
    it('should handle 502 on critical endpoints', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/user/profile', ERROR_MOCKS.badGateway).as('badGateway');

      cy.visit('/profile');
      cy.wait('@badGateway');

      cy.contains('Erro de conexão|servidor temporariamente|tente novamente').should('be.visible');
    });
  });

  // ==================== 503 SERVICE UNAVAILABLE ====================
  describe('503 Service Unavailable Errors', () => {
    it('should handle 503 on dashboard load', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/workout/stats', ERROR_MOCKS.serviceUnavailable).as('serviceUnavailable');

      cy.visit('/dashboard');
      cy.wait('@serviceUnavailable');

      cy.contains('serviço indisponível|manutenção|tente novamente').should('be.visible');
    });

    it('should handle 503 on chat endpoint', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/message/message', ERROR_MOCKS.serviceUnavailable).as('chatUnavailable');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test');
      cy.get('button').contains('Enviar').click();
      cy.wait('@chatUnavailable');

      cy.contains('serviço indisponível|tente novamente mais tarde').should('be.visible');
    });
  });

  // ==================== NETWORK ERRORS ====================
  describe('Network Errors', () => {
    it('should handle network error on message send', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/message/message', ERROR_MOCKS.networkError).as('networkError');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test message');
      cy.get('button').contains('Enviar').click();
      cy.wait('@networkError');

      cy.contains('Erro de conexão|verif|internet').should('be.visible');
    });

    it('should handle network error on stats load', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/workout/stats', ERROR_MOCKS.networkError).as('statsNetworkError');

      cy.visit('/dashboard');
      cy.wait('@statsNetworkError');

      cy.contains('Erro de conexão|internet|tente novamente').should('be.visible');
    });

    it('should allow retry after network error', () => {
      cy.mockLogin();

      // First intercept fails with network error
      cy.intercept('GET', '**/nutrition/stats', ERROR_MOCKS.networkError).as('firstAttempt');

      cy.visit('/nutrition');
      cy.wait('@firstAttempt');
      cy.contains('Erro de conexão').should('be.visible');

      // Mock success for retry
      cy.intercept('GET', '**/nutrition/stats', {
        body: { daily_calorie: 2000, macros: { protein: 150, carbs: 200, fat: 70 } }
      }).as('retrySuccess');

      cy.get('button').contains('Tentar novamente|Recarregar').click();
      cy.wait('@retrySuccess');

      cy.contains('Erro de conexão').should('not.exist');
    });
  });

  // ==================== CASCADING ERRORS ====================
  describe('Cascading Error Scenarios', () => {
    it('should handle error on profile then allow retry on chat', () => {
      cy.mockLogin();

      // Profile fails
      cy.intercept('GET', '**/user/profile', ERROR_MOCKS.serverError).as('profileError');
      cy.visit('/profile');
      cy.wait('@profileError');
      cy.contains('Erro ao carregar').should('be.visible');

      // Navigate to chat - should work with new mock
      cy.intercept('GET', '**/message/history', {
        body: [{ id: '1', text: 'test', sender: 'user', timestamp: new Date().toISOString() }]
      }).as('chatSuccess');

      cy.visit('/chat');
      cy.wait('@chatSuccess');
      cy.contains('test').should('be.visible');
    });

    it('should handle multiple simultaneous errors', () => {
      cy.mockLogin();

      // Multiple endpoints fail simultaneously
      cy.intercept('GET', '**/workout/stats', ERROR_MOCKS.serverError).as('workoutError');
      cy.intercept('GET', '**/nutrition/stats', ERROR_MOCKS.serverError).as('nutritionError');
      cy.intercept('GET', '**/weight/history', ERROR_MOCKS.serverError).as('weightError');

      cy.visit('/dashboard');
      cy.wait(['@workoutError', '@nutritionError', '@weightError']);

      // Should show general error message or placeholder
      cy.contains('Erro ao carregar|tente novamente').should('be.visible');
    });

    it('should handle timeout on long requests', () => {
      cy.mockLogin();

      // Simulate timeout with very long delay
      cy.intercept('POST', '**/message/message', {
        delay: 35000, // Longer than typical timeout
        body: { id: '1', text: 'response' }
      }).as('timeout');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test');
      cy.get('button').contains('Enviar').click();

      // Request should timeout or show timeout error
      cy.contains('Tempo esgotado|timeout|tente novamente').should('be.visible');
    });
  });

  // ==================== ERROR RECOVERY ====================
  describe('Error Recovery', () => {
    it('should retry failed request after recovery', () => {
      cy.mockLogin();

      // First request fails
      let requestCount = 0;
      cy.intercept('GET', '**/nutrition/stats', (req) => {
        requestCount++;
        if (requestCount === 1) {
          req.reply({ statusCode: 500, body: { detail: 'Error' } });
        } else {
          req.reply({ body: { daily_calorie: 2000 } });
        }
      }).as('retryableRequest');

      cy.visit('/nutrition');
      cy.wait('@retryableRequest');

      // Retry mechanism
      cy.get('button').contains('Tentar novamente|Recarregar').click();
      cy.wait('@retryableRequest');

      cy.contains('2000').should('be.visible');
    });

    it('should clear error message when user interacts', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/nutrition/log', ERROR_MOCKS.serverError).as('logError');

      cy.visit('/nutrition/log');
      cy.get('input[name="calories"]').type('2000');
      cy.get('button').contains('Registrar').click();
      cy.wait('@logError');

      // Error should be visible
      cy.contains('Erro ao registrar').should('be.visible');

      // Modify form - error should clear
      cy.get('input[name="calories"]').clear().type('1500');
      cy.contains('Erro ao registrar').should('not.exist');
    });

    it('should show retry countdown after rate limit', () => {
      cy.mockLogin();
      cy.intercept('POST', '**/message/message', ERROR_MOCKS.tooManyRequests).as('rateLimit');

      cy.visit('/chat');
      cy.get('textarea[name="message"]').type('test');
      cy.get('button').contains('Enviar').click();
      cy.wait('@rateLimit');

      // Should show retry timer
      cy.contains(/tentar|espere|segundos/).should('be.visible');
    });
  });

  // ==================== ERROR LOGGING ====================
  describe('Error Logging and Tracking', () => {
    it('should log server errors to console', () => {
      cy.mockLogin();
      cy.intercept('GET', '**/user/profile', ERROR_MOCKS.serverError).as('profileError');

      const consoleSpy = cy.spy(console, 'error');

      cy.visit('/profile');
      cy.wait('@profileError');

      // Error should be logged
      cy.wrap(consoleSpy).should('have.been.called');
    });

    it('should distinguish between client and server errors', () => {
      cy.mockLogin();

      // Client error (4xx)
      cy.intercept('GET', '**/endpoint1', ERROR_MOCKS.validationError).as('clientError');
      // Server error (5xx)
      cy.intercept('GET', '**/endpoint2', ERROR_MOCKS.serverError).as('serverError');

      cy.visit('/page1');
      cy.wait('@clientError');
      cy.contains('validação').should('be.visible');

      cy.visit('/page2');
      cy.wait('@serverError');
      cy.contains('servidor').should('be.visible');
    });
  });
});
