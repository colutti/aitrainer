import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';

import { useChatStore } from './useChat';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
  API_BASE_URL: 'http://localhost/api',
}));

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('useChatStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useChatStore.getState().reset();
  });

  // State checks
  it('should have initial state', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.isStreaming).toBe(false);
  });

  // Fetch History
  it('should fetch history successfully', async () => {
    const mockHistory = [{ text: 'Hello', sender: 'Trainer', timestamp: '2024-01-01' }];
    vi.mocked(httpClient).mockResolvedValue(mockHistory);

    await useChatStore.getState().fetchHistory();

    const state = useChatStore.getState();
    expect(state.messages).toEqual(mockHistory);
    expect(httpClient).toHaveBeenCalledWith('/message/history?limit=20&offset=0');
  });

  it('should handle fetch history error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(httpClient).mockRejectedValue(new Error('API Error'));

    await useChatStore.getState().fetchHistory();

    const state = useChatStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Falha ao carregar histórico de mensagens.');
    consoleSpy.mockRestore();
  });

  // Send Message
  it('should send message and stream response', async () => {
    const messageText = 'Hello AI';
    const streamResponse = 'Hello User';
    
    // Create a mock stream with SSE format
    const statusEvent1 = 'data: {"type": "status", "node": "session_context"}\n\n';
    const statusEvent2 = 'data: {"type": "status", "node": "training_specialist"}\n\n';
    const responseEvent = `data: {"type": "response", "text": "${streamResponse}"}\n\n`;
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(statusEvent1));
        controller.enqueue(new TextEncoder().encode(statusEvent2));
        controller.enqueue(new TextEncoder().encode(responseEvent));
        controller.close();
      }
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: {
        getReader: () => stream.getReader(),
      },
    });

    // Initial state check
    expect(useChatStore.getState().messages).toHaveLength(0);

    // Trigger send
    const sendPromise = useChatStore.getState().sendMessage(messageText);
    
    // Check optimistic update
    const stateAfterSend = useChatStore.getState();
    expect(stateAfterSend.messages).toHaveLength(1);
    expect(stateAfterSend.messages[0]?.text).toBe(messageText);
    expect(stateAfterSend.isStreaming).toBe(true);

    // Wait for completion
    await sendPromise;

    const finalState = useChatStore.getState();
    expect(finalState.isStreaming).toBe(false);
    expect(finalState.messages).toHaveLength(2); // User + AI
    expect(finalState.messages[1]?.text).toContain(streamResponse);
  });

  it('should handle send message error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetch.mockRejectedValue(new Error('Network Error'));

    await useChatStore.getState().sendMessage('Hello');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.messages).toHaveLength(1);
    expect(state.error).toBe('Ocorreu um problema ao enviar sua mensagem.');
    consoleSpy.mockRestore();
  });

  it('should handle stream timeout abort error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetch.mockRejectedValue(new DOMException('The operation was aborted.', 'AbortError'));

    await useChatStore.getState().sendMessage('Hello');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.error).toBe('A resposta demorou demais. Tente novamente.');
    consoleSpy.mockRestore();
  });

  it('should handle limit exceeded error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'LIMITE_MENSAGENS_MES' }),
    });

    await useChatStore.getState().sendMessage('Hello Limit');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.error).toBe('Você atingiu o limite de mensagens do seu plano. Atualize sua assinatura ou aguarde o próximo mês.');
    consoleSpy.mockRestore();
  });

  it('should handle trial expired error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'TRIAL_EXPIRED' }),
    });

    await useChatStore.getState().sendMessage('Hello Trial');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.error).toBe('TRIAL_EXPIRED');
    consoleSpy.mockRestore();
  });

  it('should handle daily limit reached error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'DAILY_LIMIT_REACHED' }),
    });

    await useChatStore.getState().sendMessage('Hello Daily');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.error).toBe('DAILY_LIMIT_REACHED');
    consoleSpy.mockRestore();
  });

  it('sends message with image payload when provided', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('ok'));
        controller.close();
      }
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('Analisa essa foto', [
      {
        base64: 'abc123',
        mimeType: 'image/jpeg',
      },
    ]);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/message'),
      expect.objectContaining({
        body: JSON.stringify({
          user_message: 'Analisa essa foto',
          images: [{ base64: 'abc123', mime_type: 'image/jpeg' }],
        }),
      }),
    );
  });

  it('should handle image entitlement error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetch.mockResolvedValue({
      ok: false,
      status: 403,
      json: async () => ({ detail: 'IMAGE_NOT_ALLOWED_FOR_PLAN' }),
    });

    await useChatStore.getState().sendMessage('Analisa', [
      {
        base64: 'abc123',
        mimeType: 'image/jpeg',
      },
    ]);

    const state = useChatStore.getState();
    expect(state.error).toBe('IMAGE_NOT_ALLOWED_FOR_PLAN');
    consoleSpy.mockRestore();
  });

  it('should handle message too long validation error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: [{ msg: 'Value error, MESSAGE_TOO_LONG' }] }),
    });

    await useChatStore.getState().sendMessage('x'.repeat(21000));

    const state = useChatStore.getState();
    expect(state.error).toBe('MESSAGE_TOO_LONG');
    consoleSpy.mockRestore();
  });

  it('should handle generic validation error with friendly code', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: [{ msg: 'String should have at least 1 character' }] }),
    });

    await useChatStore.getState().sendMessage('Hello');

    const state = useChatStore.getState();
    expect(state.error).toBe('VALIDATION_ERROR');
    consoleSpy.mockRestore();
  });

  it('should clear history successfully', () => {
    // Setup state
    useChatStore.setState({ messages: [{ text: 'Hi', sender: 'Student', timestamp: 'now' }] });
    
    useChatStore.getState().clearHistory();

    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
  });

  it('should never leak data: framing into rendered text when chunks are split across reads', async () => {
    const streamResponse = 'Resposta normal com acentuação';
    const statusEvent = 'event: status\ndata: {"type":"status","node":"session_context"}\n\n';
    const responseEvent = `event: response\ndata: {"type":"response","text":"${streamResponse}"}\n\n`;

    // Simulate chunked transport: each part is a partial read
    const chunks = [
      new TextEncoder().encode(statusEvent.slice(0, 20)),
      new TextEncoder().encode(statusEvent.slice(20)),
      new TextEncoder().encode(responseEvent.slice(0, 15)),
      new TextEncoder().encode(responseEvent.slice(15)),
    ];

    let chunkIndex = 0;
    const stream = new ReadableStream({
      pull(controller) {
        if (chunkIndex < chunks.length) {
          controller.enqueue(chunks[chunkIndex]);
          chunkIndex += 1;
        } else {
          controller.close();
        }
      },
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('teste');

    const state = useChatStore.getState();
    expect(state.messages).toHaveLength(2);
    const aiText = state.messages[1]?.text ?? '';
    expect(aiText).toBe(streamResponse);
    expect(aiText).not.toContain('data:');
    expect(aiText).not.toContain('event:');
  });

  it('should handle CRLF line endings in SSE stream', async () => {
    const streamResponse = 'Resposta com CRLF';
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(
          'event: status\r\ndata: {"type":"status","node":"session_context"}\r\n\r\n'
          + `event: response\r\ndata: {"type":"response","text":"${streamResponse}"}\r\n\r\n`
        ));
        controller.close();
      }
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('teste');

    const state = useChatStore.getState();
    const aiText = state.messages[1]?.text ?? '';
    expect(aiText).toBe(streamResponse);
    expect(aiText).not.toContain('data:');
  });

  it('should ignore malformed JSON payloads without leaking into visible text', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(
          'event: status\ndata: not-json!!\n\n'
          + 'event: response\ndata: {"type":"response","text":"boa resposta"}\n\n'
        ));
        controller.close();
      }
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('teste');

    const state = useChatStore.getState();
    const aiText = state.messages[1]?.text ?? '';
    expect(aiText).toBe('boa resposta');
    expect(aiText).not.toContain('not-json');
    expect(aiText).not.toContain('data:');
  });

  it('should handle stream with only status events (no response)', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(
          'event: status\ndata: {"type":"status","node":"session_context"}\n\n'
          + 'event: status\ndata: {"type":"status","node":"training_specialist"}\n\n'
        ));
        controller.close();
      }
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('teste');

    const state = useChatStore.getState();
    const aiText = state.messages[1]?.text ?? '';
    expect(aiText).toBe('');
    // Should not contain any framing
    expect(aiText).not.toContain('data:');
  });

  it('should not show escaped Unicode in rendered text', async () => {
    const escapedPayload = '{"type":"response","text":"Boa\\u0027monstro\\u0021"}';
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(
          `event: response\ndata: ${escapedPayload}\n\n`
        ));
        controller.close();
      }
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('teste');

    const state = useChatStore.getState();
    const aiText = state.messages[1]?.text ?? '';
    expect(aiText).not.toContain('\\\\u00');
    expect(aiText).not.toContain('\\u00');
    expect(aiText).not.toContain('data:');
  });
});
