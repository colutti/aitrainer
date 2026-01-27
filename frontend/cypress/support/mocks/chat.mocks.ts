/**
 * Chat-related mocks for Cypress tests
 */
export const CHAT_MOCKS = {
  emptyHistory: [],

  singleMessage: [
    {
      sender: 'ai',
      text: 'Olá! Como posso ajudar?',
      timestamp: new Date().toISOString()
    }
  ],

  conversation: [
    {
      sender: 'user',
      text: 'Qual o melhor exercício para peito?',
      timestamp: new Date(Date.now() - 60000).toISOString()
    },
    {
      sender: 'ai',
      text: 'Para peito, recomendo supino reto, supino inclinado e crucifixo.',
      timestamp: new Date().toISOString()
    }
  ],

  streamingResponse: {
    statusCode: 200,
    headers: { 'content-type': 'text/event-stream' },
    body: 'data: {"content": "Teste"}\n\ndata: {"content": " de"}\n\ndata: {"content": " resposta"}\n\ndata: [DONE]\n\n',
    delay: 500
  },

  typingIndicator: {
    statusCode: 200,
    body: { typing: true }
  },

  aiResponse: {
    statusCode: 200,
    body: {
      response: 'Esta é uma resposta de IA simulada com conteúdo útil sobre fitness.',
      typing: false
    }
  },

  errorResponse: {
    statusCode: 500,
    body: { detail: 'Erro ao processar mensagem' }
  }
};
