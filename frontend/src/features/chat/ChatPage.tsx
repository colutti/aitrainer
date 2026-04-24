import { useEffect, useRef, useMemo, useLayoutEffect, useCallback, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useChatStore } from '../../shared/hooks/useChat';
import { useSettingsStore } from '../../shared/hooks/useSettings';
import type { MessageImagePayload } from '../../shared/types/chat';

import { ChatView } from './components/ChatView';

/**
 * ChatPage component (Container)
 * 
 * Interactive AI assistant interface for health, fitness and nutrition advice.
 * Manages chat logic, streaming state, and scroll behavior.
 */
export default function ChatPage() {
  const { messages, isStreaming, error, fetchHistory, sendMessage, loadMore, hasMore, isLoading } = useChatStore();
  const { trainer, availableTrainers, fetchTrainer, fetchAvailableTrainers } = useSettingsStore();
  const { userInfo } = useAuthStore();
  
  const location = useLocation();
  const navigate = useNavigate();
  const initialDraftMessage = useMemo(() => {
    const state = location.state as { draftMessage?: string } | null;
    return state?.draftMessage?.trim() ?? '';
  }, [location.state]);
  const [draftSeed] = useState(initialDraftMessage);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  
  const prevScrollHeightRef = useRef<number>(0);
  const prevMessagesLength = useRef(0);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false);
  const isFirstRenderRef = useRef(true);
  const bootstrappedRef = useRef(false);

  // Initial data fetch on mount
  useEffect(() => {
    if (bootstrappedRef.current) return;
    bootstrappedRef.current = true;
    void fetchHistory();
    void fetchTrainer();
    void fetchAvailableTrainers();
  }, [fetchHistory, fetchTrainer, fetchAvailableTrainers]);

  useEffect(() => {
    if (!initialDraftMessage) return;
    void navigate(location.pathname, { replace: true, state: null });
  }, [initialDraftMessage, location.pathname, navigate]);

  // Find current trainer details
  const currentTrainer = useMemo(() => {
    if (!trainer) return null;
    return availableTrainers.find(t => t.trainer_id === trainer.trainer_type) ?? null;
  }, [trainer, availableTrainers]);

  // Scroll handler
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    
    // Auto-scroll detection (bottom)
    const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 50;
    setShouldAutoScroll(isAtBottom);

    // Load more detection (top)
    if (scrollTop === 0 && hasMore && !isLoading && messages.length > 0) {
      prevScrollHeightRef.current = scrollHeight;
      void loadMore();
    }
  };

  useLayoutEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const newLength = messages.length;
    // Restore scroll position logic
    if (prevScrollHeightRef.current > 0 && newLength > prevMessagesLength.current) {
      const newScrollHeight = container.scrollHeight;
      const diff = newScrollHeight - prevScrollHeightRef.current;

      // Only adjust if height actually increased (history prepended)
      if (diff > 0) {
        container.scrollTop = diff;
      }
      prevScrollHeightRef.current = 0;
    } else if (isFirstRenderRef.current && newLength > 0) {
        // First load with messages: scroll immediately (no animation)
        messagesEndRef.current?.scrollIntoView({ behavior: 'auto' } as ScrollIntoViewOptions);
        isFirstRenderRef.current = false;
    } else if (shouldAutoScroll || (newLength > prevMessagesLength.current && messages[newLength-1]?.sender === 'Student')) {
        // Auto-scroll if at bottom or user sent a message (smooth animation)
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' } as ScrollIntoViewOptions);
    }

    prevMessagesLength.current = newLength;
  }, [messages, shouldAutoScroll, isLoading]);

  const handleSend = useCallback((text: string, images?: MessageImagePayload[]) => {
    if (isStreaming) return;
    if (!text) return;
    void sendMessage(text, images);
  }, [isStreaming, sendMessage]);

  return (
    <ChatView 
      messages={messages}
      isStreaming={isStreaming}
      isLoading={isLoading}
      hasMore={hasMore}
      error={error}
      trainer={currentTrainer}
      userInfo={userInfo}
      initialInputValue={draftSeed}
      onSend={handleSend}
      onScroll={handleScroll}
      scrollContainerRef={scrollContainerRef}
      messagesEndRef={messagesEndRef}
    />
  );
}
