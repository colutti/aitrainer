import { Bot, Send } from 'lucide-react';
import { useEffect, useRef, useState, useMemo, useLayoutEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { useChatStore } from '../../shared/hooks/useChat';
import { useSettingsStore } from '../../shared/hooks/useSettings';
import { cn } from '../../shared/utils/cn';

import { MessageBubble } from './components/MessageBubble';

/**
 * ChatPage component
 * 
 * Interactive AI assistant interface for health, fitness and nutrition advice.
 * Supports real-time streaming and persistent history.
 */
export function ChatPage() {
  const { messages, isStreaming, error, fetchHistory, sendMessage, loadMore, hasMore, isLoading } = useChatStore();
  const { trainer, availableTrainers, fetchTrainer, fetchAvailableTrainers } = useSettingsStore();
  const { userInfo } = useAuthStore();
  const { t } = useTranslation();
  
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initial data fetch on mount
  useEffect(() => {
    void fetchHistory();
    void fetchTrainer();
    void fetchAvailableTrainers();
  }, [fetchHistory, fetchTrainer, fetchAvailableTrainers]);

  // Find current trainer details
  const currentTrainer = useMemo(() => {
    if (!trainer) return null;
    return availableTrainers.find(t => t.trainer_id === trainer.trainer_type) ?? null;
  }, [trainer, availableTrainers]);

  const trainerName = currentTrainer?.name ?? t('chat.default_trainer_name');

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeightRef = useRef<number>(0);
  const prevMessagesLength = useRef(0);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(false);
  const isFirstRenderRef = useRef(true);

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

  useEffect(() => {
    if (textareaRef.current) {
      const target = textareaRef.current;
      target.style.height = 'auto';
      target.style.height = `${target.scrollHeight.toString()}px`;
    }
  }, [inputValue]);

  const handleSend = async (e?: React.BaseSyntheticEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || isStreaming) return;

    const text = inputValue.trim();
    setInputValue('');
    await sendMessage(text);
  };

  return (
    <div className="fixed inset-0 bottom-16 lg:bottom-0 lg:left-64 bg-dark-bg z-40 flex flex-col">
      {/* Header - Fixed Top */}
      <div className="flex-none h-16 bg-dark-bg/80 backdrop-blur-md border-b border-white/5 px-6 flex items-center justify-between z-50">
        <div className="flex items-center gap-3 mx-auto w-full max-w-6xl">
          <div className="w-8 h-8 rounded-lg overflow-hidden border border-white/10 shrink-0">
            {currentTrainer ? (
              <img 
                src={`/assets/avatars/${currentTrainer.trainer_id.toLowerCase()}.png`} 
                alt={currentTrainer.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gradient-start flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold text-text-primary">
              {trainerName}
            </h1>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shadow-success" />
          </div>
        </div>
      </div>

      {/* Messages Area - Flexible & Scrollable */}
      <div 
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-6xl mx-auto w-full p-4 md:p-6 pb-24 space-y-6">
          {isLoading && hasMore && messages.length > 0 && (
            <div className="flex justify-center py-4">
              <div className="w-6 h-6 border-2 border-gradient-start border-t-transparent rounded-full animate-spin" />
            </div>
          )}
          
          {messages.length === 0 && !isLoading ? (
            <div className="h-[70vh] flex flex-col items-center justify-center opacity-30 select-none">
              <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-4">
                  <Bot size={32} className="text-white/50" />
              </div>
              <p className="text-base font-medium text-text-secondary">{t('chat.start_conversation')}</p>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble
                  key={`${msg.timestamp}-${i.toString()}`}
                  message={msg}
                  trainerId={currentTrainer?.trainer_id}
                  userPhoto={userInfo?.photo_base64}
                  userName={userInfo?.name}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>
      
      {/* Input Area - Fixed Bottom */}
      <div className="flex-none p-4 w-full bg-linear-to-t from-dark-bg via-dark-bg to-transparent z-50">
        <div className="max-w-6xl mx-auto w-full relative">
            {error && (
              <div className="absolute -top-12 left-0 right-0 bg-red-500/10 text-red-400 text-xs px-4 py-2 rounded-lg border border-red-500/20 text-center mb-2 animate-in slide-in-from-bottom-2">
                {error}
              </div>
            )}

            {isStreaming && (
              <div className="absolute -top-7 left-1 flex items-center gap-2 px-2 py-1 rounded-lg bg-dark-card/40 backdrop-blur-sm border border-white/5 animate-in slide-in-from-bottom-2">
                <div className="flex gap-1">
                  <span className="w-1 h-1 bg-gradient-start rounded-full animate-bounce [animation-duration:0.6s]" />
                  <span className="w-1 h-1 bg-gradient-start rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.2s]" />
                  <span className="w-1 h-1 bg-gradient-start rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.4s]" />
                </div>
                <span className="text-[10px] font-medium text-text-secondary uppercase tracking-widest">
                  {t('chat.typing', { name: trainerName })}
                </span>
              </div>
            )}

            <form 
              onSubmit={(e) => { 
                void handleSend(e); 
              }} 
              className="relative shadow-2xl rounded-2xl bg-dark-card border border-white/10 focus-within:border-gradient-start/50 focus-within:ring-1 focus-within:ring-gradient-start/20 transition-all overflow-hidden"
            >
              <textarea
                ref={textareaRef}
                placeholder={t('chat.input_placeholder', { name: trainerName.split(' ')[0] ?? '' })}
                className="w-full bg-transparent py-4 pl-5 pr-14 text-base text-text-primary placeholder:text-text-muted focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed resize-none max-h-[200px] overflow-y-auto"
                value={inputValue}
                onChange={(e) => { setInputValue(e.target.value); }} 
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    void handleSend();
                  }
                }}
                disabled={isStreaming}
                rows={1}
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isStreaming}
                className={cn(
                  "absolute right-2 bottom-3 p-2 rounded-xl transition-all",
                  inputValue.trim() && !isStreaming
                    ? "bg-gradient-start text-white hover:bg-gradient-start/90"
                    : "text-text-muted/50 cursor-not-allowed"
                )}
              >
                <Send size={18} className={cn(isStreaming && "animate-pulse")} />
              </button>
            </form>
            <p className="mt-3 text-[10px] text-center text-text-muted/40">
              {t('chat.disclaimer')}
            </p>
        </div>
      </div>
    </div>
  );
}
