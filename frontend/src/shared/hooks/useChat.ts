import i18next from 'i18next';
import { create } from 'zustand';

import { httpClient, API_BASE_URL } from '../api/http-client';
import type { ChatMessage, MessageImagePayload } from '../types/chat';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingStage: string | null;
  error: string | null;
  hasMore: boolean;
}

interface ChatActions {
  fetchHistory: () => Promise<void>;
  loadMore: () => Promise<void>;
  sendMessage: (text: string, images?: MessageImagePayload[]) => Promise<void>;
  clearHistory: () => void;
  reset: () => void;
}

type ChatStore = ChatState & ChatActions;

const AUTH_TOKEN_KEY = 'auth_token';
const CHAT_STREAM_TIMEOUT_MS = 300_000;
let historyInFlight: Promise<void> | null = null;
let loadMoreInFlight: Promise<void> | null = null;

interface StreamEventPayload {
  text?: string;
  stage?: string;
  message?: string;
  persisted?: boolean;
}

interface ParsedSseEvent {
  event: string;
  payload: StreamEventPayload;
}

function parseSseFrame(frame: string): ParsedSseEvent | null {
  const trimmed = frame.trim();
  if (!trimmed.startsWith('event:')) return null;

  const lines = trimmed.split('\n');
  const eventLine = lines.find((line) => line.startsWith('event:'));
  const dataLines = lines.filter((line) => line.startsWith('data:'));
  if (!eventLine || dataLines.length === 0) return null;

  const event = eventLine.slice('event:'.length).trim();
  const data = dataLines
    .map((line) => line.slice('data:'.length).trim())
    .join('\n');

  try {
    return {
      event,
      payload: JSON.parse(data) as StreamEventPayload,
    };
  } catch {
    return {
      event,
      payload: { text: data },
    };
  }
}

function upsertPendingTrainerMessage(messages: ChatMessage[], nextText: string, isPending: boolean): ChatMessage[] {
  const nextMessages = [...messages];
  const lastIndex = nextMessages.length - 1;
  const existing = nextMessages[lastIndex];
  if (existing?.sender !== 'Trainer') return nextMessages;
  nextMessages[lastIndex] = {
    ...existing,
    text: nextText,
    isPending,
  };
  return nextMessages;
}

function removePendingTrainerMessage(messages: ChatMessage[]): ChatMessage[] {
  if (messages.length === 0) return messages;
  const lastMessage = messages[messages.length - 1];
  if (lastMessage?.sender === 'Trainer' && lastMessage.isPending) {
    return messages.slice(0, -1);
  }
  return messages;
}

export const useChatStore = create<ChatStore>((set, _get) => ({
  messages: [],
  isLoading: false,
  isStreaming: false,
  streamingStage: null,
  error: null,
  hasMore: true,

  fetchHistory: async () => {
    if (historyInFlight) return historyInFlight;
    historyInFlight = (async () => {
      set({ isLoading: true, error: null, hasMore: true });
      try {
        const messages = await httpClient<ChatMessage[]>('/message/history?limit=20&offset=0');

        if (messages && messages.length > 0) {
          const hasMore = messages.length === 20;
          set({ messages, isLoading: false, hasMore });
        } else {
          set({
            messages: [{
              text: i18next.t('chat.welcome_message', 'Bem-vindo ao FityQ! Eu sou seu treinador e parceiro nessa jornada. Para montarmos o plano perfeito para você, me conte: Qual é a sua maior dificuldade para manter o foco hoje? Quantos dias na semana você pretende treinar? Estou pronto para começar!'),
              sender: 'Trainer',
              timestamp: new Date().toISOString(),
            }],
            isLoading: false,
            hasMore: false,
          });
        }
      } catch (error) {
        console.error('Error fetching chat history:', error);
        set({
          isLoading: false,
          error: 'Falha ao carregar histórico de mensagens.',
          hasMore: false,
        });
      } finally {
        historyInFlight = null;
      }
    })();
    return historyInFlight;
  },

  loadMore: async () => {
    if (loadMoreInFlight) return loadMoreInFlight;
    const state = _get();
    if (state.isLoading || !state.hasMore) return;
    loadMoreInFlight = (async () => {
      set({ isLoading: true });
      try {
        const currentCount = state.messages.length;
        const limit = 20;
        const newMessages = await httpClient<ChatMessage[]>(`/message/history?limit=${limit.toString()}&offset=${currentCount.toString()}`);

        if (newMessages && newMessages.length > 0) {
          set((innerState) => ({
            messages: [...newMessages, ...innerState.messages],
            isLoading: false,
            hasMore: newMessages.length === limit,
          }));
        } else {
          set({ isLoading: false, hasMore: false });
        }
      } catch (error) {
        console.error('Error loading more history:', error);
        set({ isLoading: false, hasMore: false });
      } finally {
        loadMoreInFlight = null;
      }
    })();
    return loadMoreInFlight;
  },

  sendMessage: async (text: string, images?: MessageImagePayload[]) => {
    const userMessage: ChatMessage = {
      text,
      images,
      sender: 'Student',
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage, {
        text: '',
        sender: 'Trainer',
        timestamp: new Date().toISOString(),
        isPending: true,
      }],
      isStreaming: true,
      streamingStage: 'preparing_context',
      error: null,
    }));

    let timeoutId: number | null = null;
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY);
      const controller = new AbortController();
      timeoutId = window.setTimeout(() => {
        controller.abort();
      }, CHAT_STREAM_TIMEOUT_MS);

      const response = await fetch(`${API_BASE_URL}/message`, {
        method: 'POST',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          Authorization: token ? `Bearer ${token}` : '',
          'X-Chat-Stream-Format': 'sse-v1',
          'X-User-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        },
        body: JSON.stringify({
          user_message: text,
          images: images?.map((image) => ({
            base64: image.base64,
            mime_type: image.mimeType,
          })),
        }),
      });

      if (!response.ok) {
        if (response.status === 422) {
          try {
            const errorData = await response.json() as { detail?: { msg?: string }[] };
            const messages = errorData.detail?.map((item) => item.msg ?? '').join(' ') ?? '';
            if (messages.includes('IMAGE_TOO_LARGE')) throw new Error('IMAGE_TOO_LARGE');
            if (messages.includes('TOO_MANY_IMAGES')) throw new Error('TOO_MANY_IMAGES');
            if (messages.includes('EMPTY_MESSAGE')) throw new Error('EMPTY_MESSAGE');
            if (messages.includes('MESSAGE_TOO_LONG')) throw new Error('MESSAGE_TOO_LONG');
            throw new Error('VALIDATION_ERROR');
          } catch (e: unknown) {
            if (e instanceof Error && ['IMAGE_TOO_LARGE', 'TOO_MANY_IMAGES', 'EMPTY_MESSAGE', 'MESSAGE_TOO_LONG', 'VALIDATION_ERROR'].includes(e.message)) {
              throw e;
            }
          }
        }
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
            if (errorData.detail === 'IMAGE_NOT_ALLOWED_FOR_PLAN') {
              throw new Error('IMAGE_NOT_ALLOWED_FOR_PLAN');
            }
            if (errorData.detail === 'IMAGE_TOO_LARGE') {
              throw new Error('IMAGE_TOO_LARGE');
            }
            if (errorData.detail === 'TOO_MANY_IMAGES') {
              throw new Error('TOO_MANY_IMAGES');
            }
          } catch (e: unknown) {
            if (
              e instanceof Error
              && [
                'LIMIT_EXCEEDED',
                'TRIAL_EXPIRED',
                'DAILY_LIMIT_REACHED',
                'IMAGE_NOT_ALLOWED_FOR_PLAN',
                'IMAGE_TOO_LARGE',
                'TOO_MANY_IMAGES',
              ].includes(e.message)
            ) {
              throw e;
            }
          }
        }
        throw new Error(`Cloud error: ${response.status.toString()}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('Stream not available');

      const decoder = new TextDecoder();
      let accumulatedText = '';
      let rawBuffer = '';
      let sawStructuredEvent = false;
      let sawDoneEvent = false;
      let streamErrorMessage: string | null = null;

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        rawBuffer += chunkText;

        const frames = rawBuffer.split('\n\n');
        rawBuffer = frames.pop() ?? '';

        let handledStructuredFrame = false;
        for (const frame of frames) {
          const parsed = parseSseFrame(frame);
          if (!parsed) continue;

          handledStructuredFrame = true;
          sawStructuredEvent = true;

          if (parsed.event === 'status') {
            set({ streamingStage: parsed.payload.stage ?? null });
            continue;
          }

          if (parsed.event === 'delta') {
            accumulatedText += parsed.payload.text ?? '';
            set((state) => ({
              messages: upsertPendingTrainerMessage(state.messages, accumulatedText, true),
            }));
            continue;
          }

          if (parsed.event === 'done') {
            sawDoneEvent = true;
            accumulatedText = parsed.payload.text ?? accumulatedText;
            set((state) => ({
              messages: upsertPendingTrainerMessage(state.messages, accumulatedText, false),
              isStreaming: false,
              streamingStage: null,
              error: null,
            }));
            continue;
          }

          if (parsed.event === 'error') {
            streamErrorMessage = parsed.payload.message ?? 'Ocorreu um problema ao enviar sua mensagem.';
            set((state) => ({
              messages: removePendingTrainerMessage(state.messages),
              isStreaming: false,
              streamingStage: null,
              error: streamErrorMessage,
            }));
          }
        }

        if (!handledStructuredFrame) {
          accumulatedText += chunkText;
          set((state) => ({
            messages: upsertPendingTrainerMessage(state.messages, accumulatedText, true),
          }));
        }
      }

      if (streamErrorMessage) {
        return;
      }

      if (!sawDoneEvent) {
        set({
          isStreaming: false,
          streamingStage: null,
        });
      }

      if (!accumulatedText.trim()) {
        try {
          const messages: ChatMessage[] = (await httpClient<ChatMessage[]>('/message/history?limit=20&offset=0')) ?? [];
          const latestTrainerMessage = [...messages].reverse().find((message) => message.sender === 'Trainer');
          if (latestTrainerMessage?.text.trim()) {
            set({
              messages,
              isLoading: false,
              error: null,
              hasMore: messages.length === 20,
            });
            return;
          }
        } catch (syncError) {
          console.error('Error syncing chat history after streaming:', syncError);
        }

        set((state) => ({
          messages: removePendingTrainerMessage(state.messages),
          error: sawStructuredEvent
            ? 'Ocorreu um problema ao enviar sua mensagem.'
            : state.error,
        }));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      let errorMessage = 'Ocorreu um problema ao enviar sua mensagem.';

      if (error instanceof DOMException && error.name === 'AbortError') {
        errorMessage = 'A resposta demorou demais. Tente novamente.';
      }

      if (error instanceof Error && error.message === 'LIMIT_EXCEEDED') {
        errorMessage = 'Você atingiu o limite de mensagens do seu plano. Atualize sua assinatura ou aguarde o próximo mês.';
      } else if (error instanceof Error && (error.message === 'TRIAL_EXPIRED' || error.message === 'DAILY_LIMIT_REACHED')) {
        errorMessage = error.message;
      } else if (error instanceof Error && error.message === 'IMAGE_NOT_ALLOWED_FOR_PLAN') {
        errorMessage = 'IMAGE_NOT_ALLOWED_FOR_PLAN';
      } else if (error instanceof Error && error.message === 'IMAGE_TOO_LARGE') {
        errorMessage = 'IMAGE_TOO_LARGE';
      } else if (error instanceof Error && error.message === 'TOO_MANY_IMAGES') {
        errorMessage = 'TOO_MANY_IMAGES';
      } else if (error instanceof Error && error.message === 'EMPTY_MESSAGE') {
        errorMessage = 'EMPTY_MESSAGE';
      } else if (error instanceof Error && error.message === 'MESSAGE_TOO_LONG') {
        errorMessage = 'MESSAGE_TOO_LONG';
      } else if (error instanceof Error && error.message === 'VALIDATION_ERROR') {
        errorMessage = 'VALIDATION_ERROR';
      }

      set({
        messages: removePendingTrainerMessage(_get().messages),
        isStreaming: false,
        streamingStage: null,
        error: errorMessage,
      });
    } finally {
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
    }
  },

  clearHistory: () => {
    set({ messages: [] });
  },

  reset: () => {
    historyInFlight = null;
    loadMoreInFlight = null;
      set({
        messages: [],
        isLoading: false,
        isStreaming: false,
        streamingStage: null,
        error: null,
        hasMore: true,
      });
  },
}));
