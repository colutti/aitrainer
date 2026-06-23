import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { httpClient } from '../api/http-client';

import { useChatStore } from './useChat';

vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
  API_BASE_URL: 'http://localhost/api',
}));

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('useChatStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
    useChatStore.getState().reset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('has initial state', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.isStreaming).toBe(false);
  });

  it('fetches history successfully', async () => {
    const mockHistory = [{ text: 'Hello', sender: 'Trainer', timestamp: '2024-01-01' }];
    vi.mocked(httpClient).mockResolvedValue(mockHistory);

    await useChatStore.getState().fetchHistory();

    const state = useChatStore.getState();
    expect(state.messages).toEqual(mockHistory);
    expect(httpClient).toHaveBeenCalledWith('/message/history?limit=20&offset=0');
  });

  it('handles fetch history error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(httpClient).mockRejectedValue(new Error('API Error'));

    await useChatStore.getState().fetchHistory();

    const state = useChatStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Falha ao carregar histórico de mensagens.');
    consoleSpy.mockRestore();
  });

  it('sends message and streams text response', async () => {
    const streamResponse = 'Hello User';
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('event: status\ndata: {"stage":"using_tools"}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: delta\ndata: {"text":"Hello "}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: delta\ndata: {"text":"User"}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: done\ndata: {"text":"Hello User","persisted":true}\n\n'));
        controller.close();
      },
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('Hello AI');

    const finalState = useChatStore.getState();
    expect(finalState.isStreaming).toBe(false);
    expect(finalState.messages).toHaveLength(2);
    expect(finalState.messages[1]?.text).toContain(streamResponse);
    expect(finalState.streamingStage).toBeNull();
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost/api/message',
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-Chat-Stream-Format': 'sse-v1',
        }),
      }),
    );
  });

  it('uses the done event payload when there are no delta chunks', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('event: status\ndata: {"stage":"writing_reply"}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: done\ndata: {"text":"Hello User","persisted":true}\n\n'));
        controller.close();
      },
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('Hello AI');

    const finalState = useChatStore.getState();
    expect(finalState.isStreaming).toBe(false);
    expect(finalState.messages).toHaveLength(2);
    expect(finalState.messages[1]?.text).toBe('Hello User');
    expect(httpClient).not.toHaveBeenCalledWith('/message/history?limit=20&offset=0');
  });

  it('removes the pending trainer bubble when the stream ends with an error event', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('event: status\ndata: {"stage":"using_tools"}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: error\ndata: {"message":"Desculpe, ocorreu um erro interno. Tente novamente em instantes."}\n\n'));
        controller.close();
      },
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    await useChatStore.getState().sendMessage('Hello AI');

    const finalState = useChatStore.getState();
    expect(finalState.isStreaming).toBe(false);
    expect(finalState.messages).toHaveLength(1);
    expect(finalState.error).toBe('Desculpe, ocorreu um erro interno. Tente novamente em instantes.');
    expect(finalState.streamingStage).toBeNull();
  });

  it('handles send message error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockFetch.mockRejectedValue(new Error('Network Error'));

    await useChatStore.getState().sendMessage('Hello');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    expect(state.messages).toHaveLength(1);
    expect(state.error).toBe('Ocorreu um problema ao enviar sua mensagem.');
    consoleSpy.mockRestore();
  });

  it('stores the latest streaming stage from the backend', async () => {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode('event: status\ndata: {"stage":"using_tools"}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: status\ndata: {"stage":"writing_reply"}\n\n'));
        controller.enqueue(new TextEncoder().encode('event: done\ndata: {"text":"Hello User","persisted":true}\n\n'));
        controller.close();
      },
    });

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => stream.getReader() },
    });

    const sendPromise = useChatStore.getState().sendMessage('Hello AI');
    await sendPromise;

    expect(useChatStore.getState().streamingStage).toBeNull();
  });
});
