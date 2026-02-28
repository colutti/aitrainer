import { create } from 'zustand';

import { httpClient, API_BASE_URL } from '../api/http-client';
import type { ChatMessage } from '../types/chat';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  hasMore: boolean;
}

interface ChatActions {
  fetchHistory: () => Promise<void>;
  loadMore: () => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  clearHistory: () => void;
  reset: () => void;
}

type ChatStore = ChatState & ChatActions;

const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Chat store using Zustand
 * 
 * Manages chat history and real-time message streaming with the AI trainer.
 */
export const useChatStore = create<ChatStore>((set, _get) => ({
  messages: [],
  isLoading: false,
  isStreaming: false,
  error: null,
  hasMore: true,

  fetchHistory: async () => {
    set({ isLoading: true, error: null, hasMore: true });
    try {
      // Initial fetch: limit 20, offset 0
      const messages = await httpClient<ChatMessage[]>('/message/history?limit=20&offset=0');
      
      if (messages && messages.length > 0) {
        // If we received fewer than requested, we reached the end
        const hasMore = messages.length === 20;
        set({ messages, isLoading: false, hasMore });
      } else {
        // Welcome message if zero history
        set({ 
          messages: [{
            text: 'Olá! Eu sou seu personal trainer virtual. Como posso te ajudar a atingir seus objetivos hoje?',
            sender: 'Trainer',
            timestamp: new Date().toISOString()
          }], 
          isLoading: false,
          hasMore: false
        });
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao carregar histórico de mensagens.',
        hasMore: false
      });
    }
  },

  loadMore: async () => {
    const state = _get();
    if (state.isLoading || !state.hasMore) return;

    set({ isLoading: true });
    try {
      const currentCount = state.messages.length;
      const limit = 20;
      
      // Filter out local-only welcome message if needed, but usually it's overwritten
      // Simplification: offset = currentCount
      
      const newMessages = await httpClient<ChatMessage[]>(`/message/history?limit=${limit.toString()}&offset=${currentCount.toString()}`);
      
      if (newMessages && newMessages.length > 0) {
        set((state) => ({
          messages: [...newMessages, ...state.messages],
          isLoading: false,
          hasMore: newMessages.length === limit
        }));
      } else {
        set({ isLoading: false, hasMore: false });
      }
    } catch (error) {
      console.error('Error loading more history:', error);
      set({ isLoading: false, hasMore: false }); // Don't block UI with error, just stop trying
    }
  },

  sendMessage: async (text: string) => {
    const userMessage: ChatMessage = {
      text,
      sender: 'Student',
      timestamp: new Date().toISOString(),
    };

    set((state) => ({ 
      messages: [...state.messages, userMessage],
      isStreaming: true,
      error: null
    }));

    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const response = await fetch(`${API_BASE_URL}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify({ user_message: text }),
      });

      if (!response.ok) {
        if (response.status === 403) {
          try {
            const errorData = await response.json() as { detail?: string };
            if (errorData?.detail?.includes('LIMITE')) {
              throw new Error('LIMIT_EXCEEDED');
            }
          } catch (e: unknown) {
            if (e instanceof Error && e.message === 'LIMIT_EXCEEDED') {
               throw e;
            }
          }
        }
        throw new Error(`Cloud error: ${response.status.toString()}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Stream not available');

      const aiMessage: ChatMessage = {
        text: '',
        sender: 'Trainer',
        timestamp: new Date().toISOString(),
      };

      set((state) => ({ 
        messages: [...state.messages, aiMessage] 
      }));

      const decoder = new TextDecoder();
      let accumulatedText = '';

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;

        accumulatedText += decoder.decode(value, { stream: true });

        set((state) => {
          const newMessages = [...state.messages];
          const lastIndex = newMessages.length - 1;
          const existing = newMessages[lastIndex];
          if (existing) {
            newMessages[lastIndex] = {
              ...existing,
              text: accumulatedText,
              sender: existing.sender
            };
          }
          return { messages: newMessages };
        });
      }
      
      set({ isStreaming: false });
    } catch (error) {
      console.error('Error sending message:', error);
      let errorMessage = 'Ocorreu um problema ao enviar sua mensagem.';
      
      if (error instanceof Error && error.message === 'LIMIT_EXCEEDED') {
        errorMessage = 'Você atingiu o limite de mensagens do seu plano. Atualize sua assinatura ou aguarde o próximo mês.';
      }
      
      set({ 
        isStreaming: false, 
        error: errorMessage 
      });
    }
  },

  clearHistory: () => {
    set({ messages: [] });
  },

  reset: () => {
    set({
      messages: [],
      isLoading: false,
      isStreaming: false,
      error: null,
      hasMore: true
    });
  },
}));
