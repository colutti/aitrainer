import { describe, expect, it, vi, beforeEach } from 'vitest';

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
    useChatStore.getState().reset();
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
        controller.enqueue(new TextEncoder().encode('Hello '));
        controller.enqueue(new TextEncoder().encode('User'));
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
});
