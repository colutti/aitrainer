import { Send, Sparkles, AlertCircle, Paperclip, X } from 'lucide-react';
import { memo, useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { HelpTooltip } from '../../../shared/components/ui/HelpTooltip';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import type { UserInfo } from '../../../shared/hooks/useAuth';
import { useDemoMode } from '../../../shared/hooks/useDemoMode';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import type { ChatGraphTrace, ChatMessage, MessageImagePayload } from '../../../shared/types/chat';
import type { TrainerCard } from '../../../shared/types/settings';
import { cn } from '../../../shared/utils/cn';

import { ChatContextPanel } from './ChatContextPanel';
import { ChatDebugOverlay } from './debug/ChatDebugOverlay';
import { useChatDebugInspectorState } from './debug/useChatDebugInspectorState';
import { MessageBubble } from './MessageBubble';

export interface ChatViewProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingStatus: string | null;
  isLoading: boolean;
  hasMore: boolean;
  error: string | null;
  trainer: TrainerCard | null;
  userInfo: UserInfo | null;
  debugTrace?: ChatGraphTrace | null;
  debugTraceError?: string | null;
  initialInputValue?: string;
  onSend: (text: string, images?: MessageImagePayload[]) => void | Promise<void>;
  onScroll: (e: React.UIEvent<HTMLDivElement>) => void;
  scrollContainerRef: React.RefObject<HTMLDivElement | null>;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

interface MessageListProps {
  messages: ChatMessage[];
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  trainerId?: string;
  userPhoto?: string;
  userName?: string;
  resolveText: (message: ChatMessage) => string;
}

const MessageList = memo(function MessageList({
  messages,
  messagesEndRef,
  trainerId,
  userPhoto,
  userName,
  resolveText,
}: MessageListProps) {
  return (
    <>
      {messages.map((msg, i) => (
        <MessageBubble
          key={`${msg.timestamp}-${i.toString()}`}
          message={msg}
          resolveText={resolveText}
          trainerId={trainerId}
          userPhoto={userPhoto}
          userName={userName}
        />
      ))}
      <div ref={messagesEndRef} className="h-4" />
    </>
  );
});

export function ChatView({
  messages,
  isStreaming,
  streamingStatus,
  isLoading,
  hasMore,
  error,
  trainer,
  userInfo,
  debugTrace,
  debugTraceError,
  initialInputValue = '',
  onSend,
  onScroll,
  scrollContainerRef,
  messagesEndRef,
}: ChatViewProps) {
  const { t, i18n } = useTranslation();
  const [inputValue, setInputValue] = useState(initialInputValue);
  const [selectedImages, setSelectedImages] = useState<MessageImagePayload[]>([]);
  const [selectedImagePreviews, setSelectedImagePreviews] = useState<string[]>([]);
  const [localUploadError, setLocalUploadError] = useState<string | null>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const MAX_IMAGES_PER_MESSAGE = 4;
  const MAX_IMAGE_SIZE_BYTES = 3 * 1024 * 1024;
  const maxImageSizeMb = (MAX_IMAGE_SIZE_BYTES / (1024 * 1024)).toString();
  const supportedFormatsLabel = t('chat.image_upload.supported_formats');
  const imageHintLabel = t('chat.image_upload.helper_tooltip', {
    formats: supportedFormatsLabel,
    maxImages: MAX_IMAGES_PER_MESSAGE.toString(),
    maxSizeMb: maxImageSizeMb,
  });
  const imageHelperAriaLabel = t('chat.image_upload.helper_aria');
  const typingLabel = streamingStatus != null ? ('chat.status.' + streamingStatus) : 'chat.typing';
  const trainerName = trainer?.name ?? t('chat.default_trainer_name');
  const { isReadOnly: isDemoUser } = useDemoMode(userInfo);
  const normalizedLocale = i18n.language.toLowerCase();
  const showDebugPanel = import.meta.env.DEV;
  const inspectorState = useChatDebugInspectorState();

  useEffect(() => {
    setInputValue(initialInputValue);
  }, [initialInputValue]);

  useEffect(() => {
    if (!textareaRef.current) return;
    const target = textareaRef.current;
    target.style.height = 'auto';
    target.style.height = `${target.scrollHeight.toString()}px`;
  }, [inputValue]);

  const resolveMessageText = useCallback((message: ChatMessage) => {
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
  }, [normalizedLocale]);

  const isLimitError = error === 'TRIAL_EXPIRED' || error === 'DAILY_LIMIT_REACHED';
  const canSubmit = (!!inputValue.trim() || selectedImages.length > 0) && !isStreaming && !isDemoUser;
  const resolveErrorLabel = (errorCode: string | null) => {
    if (!errorCode) return null;
    if (errorCode === 'IMAGE_TOO_LARGE') return t('chat.errors.image_too_large');
    if (errorCode === 'TOO_MANY_IMAGES') return t('chat.errors.too_many_images');
    if (errorCode === 'IMAGE_NOT_ALLOWED_FOR_PLAN') return t('chat.errors.image_not_allowed_for_plan');
    if (errorCode === 'MESSAGE_TOO_LONG') return t('chat.errors.message_too_long');
    if (errorCode === 'VALIDATION_ERROR') return t('chat.errors.validation_error');
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
        setLocalUploadError(`Formato de arquivo não suportado. Envie ${supportedFormatsLabel}.`);
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
        setLocalUploadError(`Alguns arquivos foram ignorados por formato. Envie apenas ${supportedFormatsLabel}.`);
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
    <div
      data-testid="chat-workspace"
      className={cn(
        'h-full min-h-0 bg-[color:var(--color-background)]',
        showDebugPanel && 'lg:grid lg:h-[calc(100dvh-7rem)] lg:overflow-hidden',
      )}
      style={showDebugPanel ? { gridTemplateColumns: `minmax(0,1fr) ${inspectorState.sidebarWidth.toString()}px` } : undefined}
    >
      <section
        data-testid="chat-conversation-column"
        className={cn(
          'flex min-h-0 h-full flex-col',
          showDebugPanel && 'lg:border-r lg:border-[color:var(--color-outline-variant)] lg:overflow-hidden',
        )}
      >
        <div
          ref={scrollContainerRef}
          onScroll={onScroll}
          className="flex-1 min-h-0 overflow-y-auto custom-scrollbar pt-6"
        >
          <div className="max-w-[88rem] mx-auto w-full p-4 md:p-6 pb-32 space-y-8">
            {isLoading && hasMore && messages.length > 0 && (
              <div className="flex justify-center py-4">
                <div className="w-6 h-6 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
              </div>
            )}

            {messages.length === 0 && !isLoading ? (
              <div className="h-[60vh] flex flex-col items-center justify-center opacity-30 select-none text-center">
                <div className="w-20 h-20 bg-[color:var(--color-surface-container)] rounded-3xl flex items-center justify-center mb-6 border border-[color:var(--color-outline-variant)] shadow-inner">
                  <Sparkles size={40} className="text-text-primary" />
                </div>
                <p className="text-lg font-semibold text-text-primary uppercase tracking-[0.2em]">{t('chat.start_conversation')}</p>
              </div>
            ) : (
              <>
                <MessageList
                  messages={messages}
                  messagesEndRef={messagesEndRef}
                  trainerId={trainer?.trainer_id}
                  userPhoto={userInfo?.photo_base64}
                  userName={userInfo?.name}
                  resolveText={resolveMessageText}
                />
              </>
            )}
          </div>
        </div>

        <div className="flex-none p-4 md:p-6 w-full">
          <div className="max-w-[88rem] mx-auto w-full">
            {error !== null && !isLimitError && (
              <div className="bg-[color:var(--color-error)]/10 text-[color:var(--color-error)] text-[10px] font-bold uppercase tracking-[0.05em] px-4 py-2 rounded-full border border-[color:var(--color-error)]/20 text-center mb-4 animate-in slide-in-from-bottom-2">
                <AlertCircle size={12} className="inline mr-2 -mt-0.5" />
                {resolveErrorLabel(error)}
              </div>
            )}

            {isDemoUser && (
              <div className="bg-amber-500/10 text-amber-300 text-[10px] font-bold uppercase tracking-[0.05em] px-4 py-2 rounded-full border border-amber-500/20 text-center mb-4">
                Demo read-only
              </div>
            )}

            {isStreaming && (
              <div className="flex items-center gap-3 px-3 py-1.5 rounded-full bg-[#09090b]/80 border border-[color:var(--color-outline-variant)] mb-4 w-fit">
                <div className="flex gap-1">
                  <span className="w-1 h-1 bg-zinc-300 rounded-full animate-bounce [animation-duration:0.6s]" />
                  <span className="w-1 h-1 bg-zinc-300 rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.2s]" />
                  <span className="w-1 h-1 bg-zinc-300 rounded-full animate-bounce [animation-duration:0.6s] [animation-delay:0.4s]" />
                </div>
                <span className="text-[10px] font-semibold text-text-muted uppercase tracking-[0.05em]">
                  {t(typingLabel, { name: trainerName })}
                </span>
              </div>
            )}

            {!isLimitError ? (
              <div className="surface-card rounded-[var(--radius-lg)] p-2 border-[color:var(--color-outline-variant)]">
                <form
                  data-testid="chat-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const text = inputValue.trim() || (selectedImages.length ? 'Analyze these images and provide practical guidance.' : '');
                    if (!text || isStreaming) return;
                    const result = onSend(text, selectedImages);
                    setInputValue('');
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
                    className="w-11 h-11 rounded-full bg-[color:var(--color-surface-container)] text-text-secondary"
                    onClick={() => {
                      imageInputRef.current?.click();
                    }}
                    data-testid="chat-image-trigger"
                  >
                    <Paperclip size={18} />
                  </Button>
                  <HelpTooltip
                    content={imageHintLabel}
                    className="opacity-80 mb-0.5"
                    align="start"
                    ariaLabel={imageHelperAriaLabel}
                  />
                  <textarea
                    ref={textareaRef}
                    data-testid="chat-input"
                    placeholder={t('chat.input_placeholder', { name: trainerName.split(' ')[0] })}
                    className="flex-1 bg-transparent py-3 pl-4 pr-2 text-base text-text-primary placeholder:text-text-muted focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed resize-none max-h-[200px] overflow-y-auto"
                    value={inputValue}
                    onChange={(e) => {
                      setInputValue(e.target.value);
                    }}
                    onKeyDown={(e) => {
                      if (!isDemoUser && e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        const text = inputValue.trim() || (selectedImages.length ? 'Analyze these images and provide practical guidance.' : '');
                        if (!text || isStreaming) return;
                        const result = onSend(text, selectedImages);
                        setInputValue('');
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
                      'w-11 h-11 rounded-full flex items-center justify-center transition-all duration-300  shrink-0 mb-0.5',
                      canSubmit ? 'bg-white text-black active:scale-90' : 'bg-[color:var(--color-surface-container)] text-text-muted cursor-not-allowed',
                    )}
                  >
                    <Send size={20} className={cn(isStreaming && 'animate-pulse', 'ml-0.5')} />
                  </Button>
                </form>
                {selectedImagePreviews.length > 0 && (
                  <div className="px-4 pt-2 pb-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-semibold text-text-secondary">
                        {selectedImagePreviews.length}/{MAX_IMAGES_PER_MESSAGE} imagens selecionadas
                      </span>
                      <span className="text-[10px] text-text-muted">Máx. {maxImageSizeMb}MB por imagem</span>
                    </div>
                    <div className="flex gap-2 overflow-x-auto">
                      {selectedImagePreviews.map((preview, index) => (
                        <div key={`${preview.slice(0, 20)}-${index.toString()}`} className="relative w-20 h-20 rounded-xl overflow-hidden border border-[color:var(--color-outline-variant)] shrink-0">
                          <img src={preview} alt="preview" className="w-full h-full object-cover" />
                          <button
                            type="button"
                            onClick={() => {
                              removeSelectedImageAt(index);
                            }}
                            className="absolute top-1 right-1 w-5 h-5 rounded-full bg-[color:var(--color-background)]/80 text-text-primary flex items-center justify-center"
                            data-testid={`chat-image-clear-${index.toString()}`}
                          >
                            <X size={12} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="px-4 pt-1 pb-1 flex justify-end">
                  {localUploadError && (
                    <p data-testid="chat-upload-error" className="text-[10px] text-amber-400 mt-1 text-right">
                      {localUploadError}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <PremiumCard className={cn(PREMIUM_UI.card.padding, 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)]')}>
                <div className="flex flex-col items-center text-center space-y-5">
                  <div className="w-14 h-14 bg-white/10 rounded-full flex items-center justify-center border border-white/20">
                    <Sparkles size={28} className="text-text-primary" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-text-primary tracking-tight">
                      {error === 'TRIAL_EXPIRED' ? t('chat.trial_ended.title') : t('chat.daily_limit.title')}
                    </h3>
                    <p className="mt-2 text-sm text-text-secondary font-medium leading-relaxed max-w-sm">
                      {error === 'TRIAL_EXPIRED' ? t('chat.trial_ended.description') : t('chat.daily_limit.description')}
                    </p>
                  </div>
                  <Button
                    type="button"
                    onClick={() => {
                      window.location.href = '/dashboard/settings/subscription';
                    }}
                    className="w-full max-w-xs bg-white text-black font-semibold py-3.5 px-8 rounded-full transition-transform active:scale-95  shadow-white/10"
                  >
                    {t('chat.upgrade_button')}
                  </Button>
                </div>
              </PremiumCard>
            )}
          </div>
        </div>
      </section>
      {showDebugPanel && (
        <aside className="hidden min-h-0 lg:block lg:h-full relative" style={{ width: `${inspectorState.sidebarWidth.toString()}px` }}>
          <div className="h-full min-h-0 overflow-y-scroll [scrollbar-gutter:stable] custom-scrollbar border-l border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-lowest)]">
            <ChatContextPanel
              trainerName={trainerName}
              trainerId={trainer?.trainer_id ?? null}
              isStreaming={isStreaming}
              messageCount={messages.length}
              debugTrace={debugTrace ?? null}
              debugTraceError={debugTraceError ?? null}
              showDebugPanel={showDebugPanel}
              onMaximize={() => { inspectorState.setShowOverlay(true); }}
            />
          </div>
          {/* Resize handle */}
          <div
            className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-[color:var(--color-primary)]/30 active:bg-[color:var(--color-primary)]/50 transition-colors"
            onMouseDown={(e) => {
              e.preventDefault();
              const startX = e.clientX;
              const startWidth = inspectorState.sidebarWidth;
              const onMove = (ev: MouseEvent) => {
                const newWidth = startWidth - (ev.clientX - startX);
                const clamped = Math.max(320, Math.min(900, newWidth));
                inspectorState.setSidebarWidth(clamped);
              };
              const onUp = () => {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
              };
              document.addEventListener('mousemove', onMove);
              document.addEventListener('mouseup', onUp);
            }}
          />
        </aside>
      )}
      {showDebugPanel && (
        <ChatDebugOverlay
          open={inspectorState.showOverlay}
          onClose={() => { inspectorState.setShowOverlay(false); }}
          debugTrace={debugTrace ?? null}
          debugTraceError={debugTraceError ?? null}
          isStreaming={isStreaming}
          expandedNode={inspectorState.expandedNode}
          showRawTrace={inspectorState.showRawTrace}
          activeTab={inspectorState.activeTab}
          onToggleNode={inspectorState.toggleNode}
          onToggleRawTrace={inspectorState.toggleRawTrace}
          onTabChange={inspectorState.setActiveTab}
          turnId={debugTrace?.turn_id}
        />
      )}
    </div>
  );
}
