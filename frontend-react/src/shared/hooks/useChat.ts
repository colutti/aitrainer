import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { ChatMessage } from '../types/chat';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
}

interface ChatActions {
  fetchHistory: () => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  clearHistory: () => void;
  reset: () => void;
}

type ChatStore = ChatState & ChatActions;

const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api';
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

  fetchHistory: async () => {
    set({ isLoading: true, error: null });
    try {
      const messages = await httpClient<ChatMessage[]>('/history');
      set({ messages: messages ?? [], isLoading: false });
    } catch (error) {
      console.error('Error fetching chat history:', error);
      set({ 
        isLoading: false, 
        error: 'Falha ao carregar histórico de mensagens.' 
      });
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
          newMessages[lastIndex] = { ...newMessages[lastIndex], text: accumulatedText };
          return { messages: newMessages };
        });
      }
      
      set({ isStreaming: false });
    } catch (error) {
      console.error('Error sending message:', error);
      set({ 
        isStreaming: false, 
        error: 'Ocorreu um problema ao enviar sua mensagem.' 
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
    });
  },
}));
