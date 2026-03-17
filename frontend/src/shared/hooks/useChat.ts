import i18next from 'i18next';
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
            text: i18next.t('chat.welcome_message', 'Bem-vindo ao FityQ! Eu sou seu treinador e parceiro nessa jornada. Para montarmos o plano perfeito para você, me conte: Qual é a sua maior dificuldade para manter o foco hoje? Quantos dias na semana você pretende treinar? Estou pronto para começar!'),
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
          'X-User-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
        body: JSON.stringify({ user_message: text }),
      });

      if (!response.ok) {
        if (response.status === 403) {
          try {
            const errorData = await response.json() as { detail?: string };
            if (errorData.detail?.includes('LIMITE')) {
              throw new Error('LIMIT_EXCEEDED');
            }
            if (errorData.detail === 'TRIAL_EXPIRED') {
              throw new Error('TRIAL_EXPIRED');
            }
            if (errorData.detail === 'DAILY_LIMIT_REACHED') {
              throw new Error('DAILY_LIMIT_REACHED');
            }
          } catch (e: unknown) {
            if (e instanceof Error && ['LIMIT_EXCEEDED', 'TRIAL_EXPIRED', 'DAILY_LIMIT_REACHED'].includes(e.message)) {
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
      } else if (error instanceof Error && (error.message === 'TRIAL_EXPIRED' || error.message === 'DAILY_LIMIT_REACHED')) {
        errorMessage = error.message;
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
