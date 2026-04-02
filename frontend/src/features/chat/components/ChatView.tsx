import { Bot, Send, Sparkles, AlertCircle, Paperclip, X } from 'lucide-react';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { HelpTooltip } from '../../../shared/components/ui/HelpTooltip';
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
  onSend: (params?: { event?: React.BaseSyntheticEvent; images?: MessageImagePayload[] }) => void | Promise<void>;
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
  const [selectedImages, setSelectedImages] = useState<MessageImagePayload[]>([]);
  const [selectedImagePreviews, setSelectedImagePreviews] = useState<string[]>([]);
  const [localUploadError, setLocalUploadError] = useState<string | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const MAX_IMAGES_PER_MESSAGE = 4;
  const MAX_IMAGE_SIZE_BYTES = 3 * 1024 * 1024;
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
  const canSubmit = (!!inputValue.trim() || selectedImages.length > 0) && !isStreaming && !isDemoUser;
  const resolveErrorLabel = (errorCode: string | null) => {
    if (!errorCode) return null;
    if (errorCode === 'IMAGE_TOO_LARGE') return 'Imagem muito grande. Use até 3MB por imagem.';
    if (errorCode === 'TOO_MANY_IMAGES') return 'Você pode enviar até 4 imagens por mensagem.';
    if (errorCode === 'IMAGE_NOT_ALLOWED_FOR_PLAN') return 'Análise de imagem disponível apenas para Pro e Premium.';
    return t(`errors.${errorCode}`, errorCode);
  };

  const clearSelectedImages = () => {
    setSelectedImages([]);
    setSelectedImagePreviews([]);
    setLocalUploadError(null);
    if (imageInputRef.current) imageInputRef.current.value = '';
  };

  const readFileAsDataUrl = async (file: File): Promise<string> =>
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

  const handleImageSelect = async (files?: FileList | null) => {
    if (!files || files.length === 0) return;
    setLocalUploadError(null);

    const incomingFiles = Array.from(files);
    const availableSlots = Math.max(0, MAX_IMAGES_PER_MESSAGE - selectedImages.length);
    let unsupportedCount = 0;
    let oversizedCount = 0;
    let skippedByLimit = 0;
    const acceptedFiles: File[] = [];

    for (const file of incomingFiles) {
      const supportedType = ['image/jpeg', 'image/png', 'image/webp'].includes(file.type);
      if (!supportedType) {
        unsupportedCount += 1;
        continue;
      }
      if (file.size > MAX_IMAGE_SIZE_BYTES) {
        oversizedCount += 1;
        continue;
      }
      if (acceptedFiles.length >= availableSlots) {
        skippedByLimit += 1;
        continue;
      }
      acceptedFiles.push(file);
    }

    if (acceptedFiles.length === 0) {
      if (unsupportedCount > 0) {
        setLocalUploadError('Formato não suportado. Use JPG, PNG ou WEBP.');
      } else if (oversizedCount > 0) {
        setLocalUploadError('Imagem muito grande. Use até 3MB por imagem.');
      } else if (skippedByLimit > 0 || availableSlots === 0) {
        setLocalUploadError(`Você pode anexar até ${MAX_IMAGES_PER_MESSAGE.toString()} imagens por mensagem.`);
      }
      return;
    }

    try {
      const nextImages: MessageImagePayload[] = [];
      const nextPreviews: string[] = [];
      for (const file of acceptedFiles) {
        const dataUrl = await readFileAsDataUrl(file);
        const [, base64Part] = dataUrl.split(',');
        if (!base64Part) continue;
        nextImages.push({
          base64: base64Part,
          mimeType: file.type as MessageImagePayload['mimeType'],
        });
        nextPreviews.push(dataUrl);
      }
      setSelectedImages((prev) => [...prev, ...nextImages]);
      setSelectedImagePreviews((prev) => [...prev, ...nextPreviews]);
      if (unsupportedCount > 0) {
        setLocalUploadError('Alguns arquivos foram ignorados: formato não suportado (use JPG, PNG ou WEBP).');
      } else if (oversizedCount > 0) {
        setLocalUploadError('Alguns arquivos foram ignorados por tamanho (máximo 3MB por imagem).');
      } else if (skippedByLimit > 0) {
        setLocalUploadError(`Limite de ${MAX_IMAGES_PER_MESSAGE.toString()} imagens por mensagem atingido.`);
      }
    } catch {
      clearSelectedImages();
    }
  };

  const removeSelectedImageAt = (index: number) => {
    setSelectedImages((prev) => prev.filter((_, i) => i !== index));
    setSelectedImagePreviews((prev) => prev.filter((_, i) => i !== index));
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
                {resolveErrorLabel(error)}
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
                    const result = onSend({ event: e, images: selectedImages });
                    clearSelectedImages();
                    if (result instanceof Promise) void result;
                  }} 
                  className="flex items-end gap-2"
                >
                  <input
                    ref={imageInputRef}
                    data-testid="chat-image-input"
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      void handleImageSelect(e.target.files);
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
                        const result = onSend({ images: selectedImages });
                        clearSelectedImages();
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
                {selectedImagePreviews.length > 0 && (
                  <div className="px-4 pt-2 pb-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-semibold text-zinc-400">
                        {selectedImagePreviews.length}/{MAX_IMAGES_PER_MESSAGE} imagens selecionadas
                      </span>
                      <span className="text-[10px] text-zinc-500">
                        Máx. {MAX_IMAGE_SIZE_BYTES / (1024 * 1024)}MB por imagem
                      </span>
                    </div>
                    <div className="flex gap-2 overflow-x-auto">
                      {selectedImagePreviews.map((preview, index) => (
                        <div key={`${preview.slice(0, 20)}-${index.toString()}`} className="relative w-20 h-20 rounded-xl overflow-hidden border border-white/10 shrink-0">
                          <img src={preview} alt="preview" className="w-full h-full object-cover" />
                          <button
                            type="button"
                            onClick={() => { removeSelectedImageAt(index); }}
                            className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/70 text-white flex items-center justify-center"
                            data-testid={`chat-image-clear-${index.toString()}`}
                          >
                            <X size={12} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="px-4 pt-1 pb-1 flex items-center justify-between">
                  <HelpTooltip
                    content="Anexe até 4 imagens por mensagem (JPG, PNG ou WEBP, máximo de 3MB cada)."
                    className="opacity-80"
                  />
                  {localUploadError && (
                    <p
                      data-testid="chat-upload-error"
                      className="text-[10px] text-amber-400 mt-1 text-right"
                    >
                      {localUploadError}
                    </p>
                  )}
                </div>
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
