import { Bot, Send, Sparkles, AlertCircle, Paperclip, X } from 'lucide-react';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import type { UserInfo } from '../../../shared/hooks/useAuth';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import type { ChatMessage, MessageImagePayload } from '../../../shared/types/chat';
import type { TrainerCard } from '../../../shared/types/settings';
import { cn } from '../../../shared/utils/cn';

import { MessageBubble } from './MessageBubble';

export interface ChatViewProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  isLoading: boolean;
  hasMore: boolean;
  error: string | null;
  trainer: TrainerCard | null;
  userInfo: UserInfo | null;
  inputValue: string;
  setInputValue: (val: string) => void;
  onSend: (params?: { event?: React.BaseSyntheticEvent; image?: MessageImagePayload | null }) => void | Promise<void>;
  onScroll: (e: React.UIEvent<HTMLDivElement>) => void;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}

export function ChatView({
  messages,
  isStreaming,
  isLoading,
  hasMore,
  error,
  trainer,
  userInfo,
  inputValue,
  setInputValue,
  onSend,
  onScroll,
  scrollContainerRef,
  messagesEndRef,
  textareaRef,
}: ChatViewProps) {
  const { t, i18n } = useTranslation();
  const [selectedImage, setSelectedImage] = useState<MessageImagePayload | null>(null);
  const [selectedImagePreview, setSelectedImagePreview] = useState<string | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const trainerName = trainer?.name ?? t('chat.default_trainer_name');
  const { isReadOnly: isDemoUser } = useDemoMode(userInfo);
  const normalizedLocale = i18n.language.toLowerCase();

  const resolveMessageText = (message: ChatMessage) => {
    if (normalizedLocale.startsWith('pt')) {
      const translated = message.translations?.['pt-BR'] ?? message.translations?.pt;
      if (translated?.trim()) return translated;
      return message.text;
    }

    if (normalizedLocale.startsWith('es')) {
      const translated = message.translations?.['es-ES'] ?? message.translations?.es;
      if (translated?.trim()) return translated;
      return message.text;
    }

    return message.text;
  };

  const isLimitError = error === 'TRIAL_EXPIRED' || error === 'DAILY_LIMIT_REACHED';
  const canSubmit = (!!inputValue.trim() || !!selectedImage) && !isStreaming && !isDemoUser;

  const clearSelectedImage = () => {
    setSelectedImage(null);
    setSelectedImagePreview(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
  };

  const handleImageSelect = async (file?: File | null) => {
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return;

    const readDataUrl = () =>
      new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          if (typeof reader.result === 'string') resolve(reader.result);
          else reject(new Error('Invalid image data'));
        };
        reader.onerror = () => {
          reject(new Error('Failed to read file'));
        };
        reader.readAsDataURL(file);
      });

    try {
      const dataUrl = await readDataUrl();
      const [, base64Part] = dataUrl.split(',');
      if (!base64Part) return;
      setSelectedImage({
        base64: base64Part,
        mimeType: file.type as MessageImagePayload['mimeType'],
      });
      setSelectedImagePreview(dataUrl);
    } catch {
      clearSelectedImage();
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0 relative overflow-hidden">
      
      {/* CHAT HEADER (DOCK STYLE) */}
      <div className="flex-none h-16 md:h-20 bg-[#09090b]/60 backdrop-blur-xl border-b border-white/5 px-6 flex items-center justify-between z-50">
        <div className="flex items-center gap-3 mx-auto w-full max-w-6xl">
          <div className="w-10 h-10 rounded-xl overflow-hidden border border-white/10 shrink-0 bg-zinc-800">
            {trainer ? (
              <img 
                src={`/assets/avatars/${trainer.trainer_id.toLowerCase()}.png`} 
                alt={trainerName}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-indigo-500">
                <Bot size={20} className="text-white" />
              </div>
            )}
          </div>
          <div>
            <h1 className="text-sm font-black text-white tracking-tight uppercase leading-tight">
              {trainerName}
            </h1>
            <div className="flex items-center gap-1.5 mt-0.5">
               <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse" />
               <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{t('chat.online_now', 'Online')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* MESSAGES AREA */}
      <div 
        ref={scrollContainerRef}
        onScroll={onScroll}
        className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pt-6"
      >
        <div className="max-w-6xl mx-auto w-full p-4 md:p-6 pb-32 space-y-8">
          {isLoading && hasMore && messages.length > 0 && (
            <div className="flex justify-center py-4">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
          
          {messages.length === 0 && !isLoading ? (
            <div className="h-[60vh] flex flex-col items-center justify-center opacity-30 select-none text-center">
              <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center mb-6 border border-white/5 shadow-inner">
                  <Sparkles size={40} className="text-white" />
              </div>
              <p className="text-lg font-black text-white uppercase tracking-[0.2em]">{t('chat.start_conversation')}</p>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble
                  key={`${msg.timestamp}-${i.toString()}`}
                  message={msg}
                  resolveText={resolveMessageText}
                  trainerId={trainer?.trainer_id}
                  userPhoto={userInfo?.photo_base64}
                  userName={userInfo?.name}
                />
              ))}
              <div ref={messagesEndRef} className="h-4" />
            </>
          )}
        </div>
      </div>

      {/* INPUT AREA (FLOATING PILL) */}
      <div className="flex-none p-4 md:p-6 w-full z-50">
        <div className="max-w-6xl mx-auto w-full">
            {error !== null && !isLimitError && (
              <div className="bg-red-500/10 text-red-400 text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-full border border-red-500/20 text-center mb-4 backdrop-blur-md animate-in slide-in-from-bottom-2">
                <AlertCircle size={12} className="inline mr-2 -mt-0.5" />
                {t(`errors.${error}`, error)}
              </div>
            )}

            {isDemoUser && (
              <div className="bg-amber-500/10 text-amber-300 text-[10px] font-bold uppercase tracking-widest px-4 py-2 rounded-full border border-amber-500/20 text-center mb-4 backdrop-blur-md">
                Demo read-only
              </div>
            )}

            {isStreaming && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#09090b]/80 border border-white/5 backdrop-blur-md mb-4 w-fit">
                <div className="flex gap-1">
                  <span className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce [animation-duration:0.6s]" />
                  <span className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.2s]" />
                  <span className="w-1 h-1 bg-indigo-500 rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.4s]" />
                </div>
                <span className="text-[10px] font-black text-zinc-500 uppercase tracking-widest">
                  {t('chat.typing', { name: trainerName })}
                </span>
              </div>
            )}

            {!isLimitError ? (
              <div className="bg-zinc-900/90 backdrop-blur-2xl border border-white/10 rounded-[32px] shadow-2xl ring-1 ring-white/5 p-2 group focus-within:ring-indigo-500/30 transition-all">
                <form 
                  data-testid="chat-form"
                  onSubmit={(e) => { 
                    const result = onSend({ event: e, image: selectedImage });
                    clearSelectedImage();
                    if (result instanceof Promise) void result;
                  }} 
                  className="flex items-end gap-2"
                >
                  <input
                    ref={imageInputRef}
                    data-testid="chat-image-input"
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={(e) => {
                      void handleImageSelect(e.target.files?.[0] ?? null);
                    }}
                    disabled={isStreaming || isDemoUser}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    disabled={isStreaming || isDemoUser}
                    className="w-11 h-11 rounded-full bg-white/5 text-zinc-200"
                    onClick={() => { imageInputRef.current?.click(); }}
                    data-testid="chat-image-trigger"
                  >
                    <Paperclip size={18} />
                  </Button>
                  <textarea
                    ref={textareaRef}
                    data-testid="chat-input"
                    placeholder={t('chat.input_placeholder', { name: trainerName.split(' ')[0] })}
                    className="flex-1 bg-transparent py-3 pl-4 pr-2 text-base text-white placeholder:text-zinc-600 focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed resize-none max-h-[200px] overflow-y-auto"
                    value={inputValue}
                    onChange={(e) => { setInputValue(e.target.value); }} 
                    onKeyDown={(e) => {
                      if (!isDemoUser && e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const result = onSend({ image: selectedImage });
                        clearSelectedImage();
                        if (result instanceof Promise) void result;
                      }
                    }}
                    disabled={isStreaming || isDemoUser}
                    rows={1}
                  />
                  <Button
                    type="submit"
                    variant="ghost"
                    size="icon"
                    disabled={!canSubmit}
                    className={cn(
                      "w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg shrink-0 mb-0.5",
                      canSubmit
                        ? "bg-white text-black active:scale-90"
                        : "bg-white/5 text-zinc-700 cursor-not-allowed"
                    )}
                  >
                    <Send size={20} className={cn(isStreaming && "animate-pulse", "ml-0.5")} />
                  </Button>
                </form>
                {selectedImagePreview && (
                  <div className="px-4 pt-2 pb-1">
                    <div className="relative w-20 h-20 rounded-xl overflow-hidden border border-white/10">
                      <img src={selectedImagePreview} alt="preview" className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={clearSelectedImage}
                        className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/70 text-white flex items-center justify-center"
                        data-testid="chat-image-clear"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <PremiumCard className={cn(PREMIUM_UI.card.padding, "bg-gradient-to-br from-indigo-900/20 to-purple-900/10 border-indigo-500/30")}>
                <div className="flex flex-col items-center text-center space-y-5">
                  <div className="w-14 h-14 bg-indigo-500/20 rounded-full flex items-center justify-center border border-indigo-500/30">
                    <Sparkles size={28} className="text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-black text-white tracking-tight">
                      {error === 'TRIAL_EXPIRED' ? t('chat.trial_ended.title') : t('chat.daily_limit.title')}
                    </h3>
                    <p className="mt-2 text-sm text-zinc-400 font-medium leading-relaxed max-w-sm">
                      {error === 'TRIAL_EXPIRED' ? t('chat.trial_ended.description') : t('chat.daily_limit.description')}
                    </p>
                  </div>
                  <Button
                    type="button"
                    onClick={() => { window.location.href = '/dashboard/settings/subscription'; }}
                    className="w-full max-w-xs bg-white text-black font-black py-3.5 px-8 rounded-full transition-transform active:scale-95 shadow-xl shadow-white/10"
                  >
                    {t('chat.upgrade_button')}
                  </Button>
                </div>
              </PremiumCard>
            )}
        </div>
      </div>
    </div>
  );
}
