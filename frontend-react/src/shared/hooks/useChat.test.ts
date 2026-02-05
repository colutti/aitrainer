import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';

import { useChatStore } from './useChat';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useChatStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useChatStore.getState().reset();
  });

  it('should have initial state', () => {
    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.isStreaming).toBe(false);
  });

  it('should fetch history successfully', async () => {
    const mockHistory = [{ text: 'Hello', sender: 'Trainer', timestamp: '2024-01-01' }];
    vi.mocked(httpClient).mockResolvedValue(mockHistory);

    await useChatStore.getState().fetchHistory();

    const state = useChatStore.getState();
    expect(state.messages).toEqual(mockHistory);
    expect(httpClient).toHaveBeenCalledWith('/message/history');
  });

  it('should clear history successfully', () => {
    useChatStore.getState().clearHistory();

    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
  });
});
