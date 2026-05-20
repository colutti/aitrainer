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

  it('syncs chat history after a blank stream so the final response appears without refresh', async () => {
    vi.useFakeTimers();

    const emptyStream = new ReadableStream({
      start(controller) {
        controller.close();
      },
    });

    const syncedHistory = [
      { text: 'Hello AI', sender: 'Student', timestamp: '2024-01-01T10:00:00Z' },
      { text: 'Hello User', sender: 'Trainer', timestamp: '2024-01-01T10:00:01Z' },
    ];

    mockFetch.mockResolvedValue({
      ok: true,
      body: { getReader: () => emptyStream.getReader() },
    });
    vi.mocked(httpClient).mockResolvedValueOnce(syncedHistory);

    const sendPromise = useChatStore.getState().sendMessage('Hello AI');
    await vi.advanceTimersByTimeAsync(500);
    await sendPromise;

    const finalState = useChatStore.getState();
    expect(finalState.isStreaming).toBe(false);
    expect(finalState.messages).toEqual(syncedHistory);
    expect(httpClient).toHaveBeenCalledWith('/message/history?limit=20&offset=0');
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
