interface ChatContextPanelProps {
  trainerName: string;
  trainerId: string | null;
  isStreaming: boolean;
  messageCount: number;
}

export function ChatContextPanel({ trainerName, trainerId, isStreaming, messageCount }: ChatContextPanelProps) {
  return (
    <div className="surface-card h-full p-4 md:p-5">
      <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">Trainer</p>
      <h2 data-testid="chat-context-trainer-name" className="mt-2 text-lg font-black text-[color:var(--color-text-primary)]">
        {trainerName}
      </h2>
      <p className="mt-4 text-sm text-[color:var(--color-text-secondary)]">
        {isStreaming ? 'Responding now' : `${messageCount.toString()} messages in this conversation`}
      </p>
      <p className="mt-2 text-xs uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
        {trainerId ?? 'default-trainer'}
      </p>
    </div>
  );
}
