import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';

import { useChatStore } from './useChat';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
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
    vi.mocked(httpClient).mockRejectedValue(new Error('API Error'));

    await useChatStore.getState().fetchHistory();

    const state = useChatStore.getState();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBe('Falha ao carregar histórico de mensagens.');
  });

  // Send Message
  it('should send message and stream response', async () => {
    const messageText = 'Hello AI';
    const streamResponse = 'Hello User';
    
    // Create a mock stream
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(streamResponse));
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
    mockFetch.mockRejectedValue(new Error('Network Error'));

    await useChatStore.getState().sendMessage('Hello');

    const state = useChatStore.getState();
    expect(state.isStreaming).toBe(false);
    // User message should still be there
    expect(state.messages).toHaveLength(1);
    // Error state set? Implementation sets error string.
    // console.error is called, verify side effect or error state if exposed
     // Implementation sets error: 'Ocorreu um problema ao enviar sua mensagem.' 
     // but the interface shows `error: string | null`.
     // Let's check logic: `set({ isStreaming: false, error: '...' })`.
     
     // Note: implementation doesn't expose `error` in `useChatStore` selector return in the way we usually test, 
     // but `useChatStore.getState()` returns the full state.
     // Is `error` part of the state?
     // Yes: `interface ChatState { ... error: string | null }`
     
    // Wait, the implementation sets error on catch block.
    // However, TypeScript definition in `useChat.ts` -> `useChatStore = create<ChatStore>`
    // The implementation might not be exposing error?
    // Let's check `useChat.ts` line 30: `create<ChatStore>((set, _get) => ({ ... error: null ...`
    // Yes it is exposed.
    
    // Wait for async execution? 
    // `sendMessage` is async. We await it.
    
    expect(state.error).toBe('Ocorreu um problema ao enviar sua mensagem.');
  });

  it('should clear history successfully', () => {
    // Setup state
    useChatStore.setState({ messages: [{ text: 'Hi', sender: 'Student', timestamp: 'now' }] });
    
    useChatStore.getState().clearHistory();

    const state = useChatStore.getState();
    expect(state.messages).toEqual([]);
  });
});
