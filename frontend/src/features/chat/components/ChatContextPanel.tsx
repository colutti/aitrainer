import { useTranslation } from 'react-i18next';

interface ChatContextPanelProps {
  trainerName: string;
  trainerId: string | null;
  isStreaming: boolean;
  messageCount: number;
}

export function ChatContextPanel({ trainerName, trainerId, isStreaming, messageCount }: ChatContextPanelProps) {
  const { t } = useTranslation();

  return (
    <div className="surface-card h-full p-4 md:p-5">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
        {t('chat.context.trainer_label')}
      </p>
      <h2 data-testid="chat-context-trainer-name" className="mt-2 text-lg font-black text-[color:var(--color-text-primary)]">
        {trainerName}
      </h2>
      <p className="mt-4 text-sm text-[color:var(--color-text-secondary)]">
        {isStreaming
          ? t('chat.context.responding_now')
          : t('chat.context.message_count', { count: messageCount })}
      </p>
      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
        {trainerId ?? t('chat.context.default_trainer_id')}
      </p>
    </div>
  );
}
