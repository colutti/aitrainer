import { Bot, Send } from 'lucide-react';
import { useEffect, useRef, useState, useMemo, useLayoutEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

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
  const navigate = useNavigate();
  
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
    <div className="fixed inset-0 bottom-16 md:bottom-18 lg:bottom-0 lg:left-64 bg-dark-bg z-40 flex flex-col">
      {/* Header - Fixed Top */}
      <div className="flex-none h-16 bg-dark-bg/80 backdrop-blur-md border-b border-border px-6 flex items-center justify-between z-50">
        <div className="flex items-center gap-3 mx-auto w-full max-w-6xl">
          <div className="w-8 h-8 rounded overflow-hidden border border-white/10 shrink-0">
            {currentTrainer ? (
              <img 
                src={`/assets/avatars/${currentTrainer.trainer_id.toLowerCase()}.png`} 
                alt={currentTrainer.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-primary flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-black text-text-primary tracking-tight uppercase">
              {trainerName}
            </h1>
            <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]" />
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
              <div className="w-16 h-16 bg-white/5 rounded-xl flex items-center justify-center mb-6 border border-white/5">
                  <Bot size={32} className="text-white" />
              </div>
              <p className="text-base font-black text-text-secondary uppercase tracking-widest">{t('chat.start_conversation')}</p>
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
            {error && !['TRIAL_EXPIRED', 'DAILY_LIMIT_REACHED'].includes(error) && (
              <div className="absolute -top-12 left-0 right-0 bg-red-500/10 text-red-400 text-xs px-4 py-2 rounded-lg border border-red-500/20 text-center mb-2 animate-in slide-in-from-bottom-2">
                {t(`errors.${error}`, error)}
              </div>
            )}

            {isStreaming && (
              <div className="absolute -top-7 left-1 flex items-center gap-2 px-2.5 py-1 rounded bg-dark-bg border border-border">
                <div className="flex gap-1">
                  <span className="w-1 h-1 bg-primary rounded-full animate-bounce [animation-duration:0.6s]" />
                  <span className="w-1 h-1 bg-primary rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.2s]" />
                  <span className="w-1 h-1 bg-primary rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.4s]" />
                </div>
                <span className="text-[10px] font-black text-text-muted uppercase tracking-widest">
                  {t('chat.typing', { name: trainerName })}
                </span>
              </div>
            )}

            {!['TRIAL_EXPIRED', 'DAILY_LIMIT_REACHED'].includes(error ?? '') ? (
              <>
                <form 
                  onSubmit={(e) => { 
                    void handleSend(e); 
                  }} 
                  className="relative rounded-xl bg-dark-card border border-border focus-within:border-primary/50 transition-colors overflow-hidden"
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
                      "absolute right-2 bottom-2.5 p-2.5 rounded-lg transition-colors duration-150",
                      inputValue.trim() && !isStreaming
                        ? "bg-primary text-white"
                        : "text-text-muted/40 cursor-not-allowed"
                    )}
                  >
                    <Send size={18} className={cn(isStreaming && "animate-pulse")} />
                  </button>
                </form>
                <div className="mt-3 flex items-center justify-between px-1">
                  <div className="flex items-center gap-4">
                    {typeof userInfo?.effective_remaining_messages === 'number' && (
                      <div className="flex items-center gap-1.5 px-2 py-1 rounded border border-white/10 bg-white/2">
                        <span className="text-[10px] text-text-primary font-bold">
                          {(userInfo.current_plan_limit ?? 100) - (userInfo.effective_remaining_messages ?? 0)}
                          <span className="text-text-muted/40 font-medium ml-0.5">/ {userInfo.current_plan_limit ?? 100}</span>
                        </span>
                        <span className="text-[10px] text-text-muted uppercase tracking-tight font-medium">
                          {t('common.msgs')}
                        </span>
                      </div>
                    )}
                    {typeof userInfo?.trial_remaining_days === 'number' && (
                      <span className="text-[10px] text-text-muted/60 font-bold bg-white/5 px-2 py-1 rounded-lg border border-white/5">
                        {t('common.days_left', { count: userInfo.trial_remaining_days })}
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-text-muted/40">
                    {t('chat.disclaimer')}
                  </p>
                </div>
              </>
            ) : (
              <div className="bg-dark-card border border-primary/30 rounded-xl p-5 sm:p-6">
                <div className="flex flex-col items-center text-center space-y-4">
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                    <Bot size={24} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-text-primary tracking-tight">
                      {error === 'TRIAL_EXPIRED' ? t('chat.trial_ended.title') : t('chat.daily_limit.title')}
                    </h3>
                    <p className="mt-2 text-sm text-text-muted font-medium leading-relaxed">
                      {error === 'TRIAL_EXPIRED' ? t('chat.trial_ended.description') : t('chat.daily_limit.description')}
                    </p>
                  </div>
                  <div className="flex flex-col sm:flex-row gap-3 w-full max-w-sm">
                    <button 
                      onClick={() => { void navigate('/dashboard/settings/subscription'); }}
                      className="flex-1 bg-primary text-white font-black py-3 px-6 rounded-lg transition-colors"
                    >
                      {t('chat.upgrade_button')}
                    </button>
                    {error === 'DAILY_LIMIT_REACHED' && (
                      <button 
                        onClick={() => { window.location.reload(); }}
                        className="flex-1 bg-white/5 text-text-primary font-bold py-3 px-6 rounded-lg transition-colors border border-border"
                      >
                        {t('chat.wait_tomorrow')}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
        </div>
      </div>
    </div>
  );
}
