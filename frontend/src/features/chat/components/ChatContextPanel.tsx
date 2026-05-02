import { useTranslation } from 'react-i18next';

import type { ChatGraphNodeTrace, ChatGraphTrace } from '../../../shared/types/chat';
import { cn } from '../../../shared/utils/cn';

interface ChatContextPanelProps {
  trainerName: string;
  trainerId: string | null;
  isStreaming: boolean;
  messageCount: number;
  debugTrace?: ChatGraphTrace | null;
  debugTraceError?: string | null;
  showDebugPanel?: boolean;
}

const formatDuration = (durationMs?: number | null): string => {
  if (typeof durationMs !== 'number' || Number.isNaN(durationMs)) {
    return '--';
  }
  if (durationMs < 1000) {
    return `${durationMs.toString()}ms`;
  }
  return `${(durationMs / 1000).toFixed(1)}s`;
};

const getNodeStatusClasses = (status: string, hasStarted: boolean): string => {
  if (status === 'completed' || status === 'success') {
    return 'border-emerald-500/30 bg-emerald-500/10';
  }
  if (status === 'failed' || status === 'error') {
    return 'border-red-500/30 bg-red-500/10';
  }
  if (status === 'pending' && !hasStarted) {
    return 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] opacity-60';
  }
  if (status === 'pending') {
    return 'border-amber-500/30 bg-amber-500/10';
  }
  if (status === 'skipped_disabled') {
    return 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)] opacity-60';
  }
  return 'border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-low)]';
};

export function ChatContextPanel({
  trainerName: _trainerName,
  trainerId: _trainerId,
  isStreaming,
  messageCount: _messageCount,
  debugTrace,
  debugTraceError,
  showDebugPanel = false,
}: ChatContextPanelProps) {
  const { t } = useTranslation();
  const nodeStatuses: Record<string, string> = {
    completed: t('chat.debug.status.completed'),
    skipped_disabled: t('chat.debug.status.skipped_disabled'),
    failed: t('chat.debug.status.failed'),
    pending: t('chat.debug.status.pending'),
    error: t('chat.debug.status.error'),
    success: t('chat.debug.status.success'),
    not_called: t('chat.debug.status.not_called'),
  };
  const traceNodes: ChatGraphNodeTrace[] =
    (debugTrace?.nodes ?? []).length > 0
      ? (debugTrace?.nodes ?? [])
      : Object.entries(debugTrace?.node_outputs ?? {}).map(([nodeName, outputPreview]) => ({
          node_name: nodeName,
          status: 'success',
          output_preview: outputPreview,
          duration_ms: null,
        }));

  return (
    <div className="surface-card relative isolate flex h-full min-h-0 flex-col overflow-hidden p-4 md:p-5" data-testid="chat-context-panel">
      {showDebugPanel && (
        <section className="flex min-h-0 flex-1 flex-col">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                {t('chat.debug.title')}
              </p>
            </div>
            {debugTrace && (
              <span className={cn(
                'rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]',
                debugTrace.status === 'success'
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                  : 'border-amber-500/30 bg-amber-500/10 text-amber-300',
              )}>
                {nodeStatuses[debugTrace.status] ?? debugTrace.status}
              </span>
            )}
          </div>

          {!debugTrace ? (
            <div className="mt-4 space-y-3">
              <p className="text-sm text-[color:var(--color-text-secondary)]">
                {isStreaming ? t('chat.debug.loading') : t('chat.debug.no_data')}
              </p>
              {debugTraceError && (
                <p className="rounded-2xl border border-[color:var(--color-error)]/20 bg-[color:var(--color-error)]/10 px-3 py-2 text-xs text-[color:var(--color-error)]">
                  {debugTraceError}
                </p>
              )}
            </div>
          ) : (
            <div className="mt-4 flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pr-1 custom-scrollbar">
              <dl className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <dt className="text-[color:var(--color-text-muted)] uppercase tracking-[0.14em]">{t('chat.debug.intent')}</dt>
                  <dd className="mt-1 text-[color:var(--color-text-primary)]">{debugTrace.intent}</dd>
                </div>
                <div>
                  <dt className="text-[color:var(--color-text-muted)] uppercase tracking-[0.14em]">{t('chat.debug.duration_total')}</dt>
                  <dd className="mt-1 text-[color:var(--color-text-primary)]">{formatDuration(debugTrace.duration_ms)}</dd>
                </div>
                <div>
                  <dt className="text-[color:var(--color-text-muted)] uppercase tracking-[0.14em]">{t('chat.debug.security')}</dt>
                  <dd className="mt-1 text-[color:var(--color-text-primary)]">{debugTrace.security_status}</dd>
                </div>
                <div>
                  <dt className="text-[color:var(--color-text-muted)] uppercase tracking-[0.14em]">{t('chat.debug.revision')}</dt>
                  <dd className="mt-1 text-[color:var(--color-text-primary)]">{debugTrace.plan_needs_revision ? t('common.yes') : t('common.no')}</dd>
                </div>
              </dl>

              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  {t('chat.debug.identifiers')}
                </p>
                <div className="mt-2 space-y-1 text-xs text-[color:var(--color-text-secondary)]">
                  <p><span className="text-[color:var(--color-text-muted)]">{t('chat.debug.request_id')}:</span> <span className="font-mono">{debugTrace.request_id}</span></p>
                  <p><span className="text-[color:var(--color-text-muted)]">{t('chat.debug.turn_id')}:</span> <span className="font-mono">{debugTrace.turn_id}</span></p>
                </div>
              </div>

              <div>
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  {t('chat.debug.tools')}
                </p>
                <p className="mt-2 text-xs text-[color:var(--color-text-secondary)]">
                  {debugTrace.tools_called.length > 0 ? debugTrace.tools_called.join(', ') : t('chat.debug.none')}
                </p>
              </div>

              <div className="flex flex-col">
                <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
                  {t('chat.debug.nodes_title')}
                </p>
                <div className="mt-3 space-y-2">
                  {traceNodes.map((node) => {
                    const hasStarted = !!node.started_at;
                    const isNotCalled = node.status === 'pending' && !hasStarted;
                    const displayStatus = isNotCalled ? 'not_called' : node.status;
                    return (
                      <div
                        key={node.node_name}
                        className={cn(
                          'rounded-2xl border p-3',
                          getNodeStatusClasses(node.status, hasStarted),
                        )}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-[color:var(--color-text-primary)]">{node.node_name}</p>
                            <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-[color:var(--color-text-muted)]">
                              {nodeStatuses[displayStatus] ?? displayStatus}
                            </p>
                          </div>
                          <span className="text-[10px] font-mono text-[color:var(--color-text-muted)]">
                            {formatDuration(node.duration_ms)}
                          </span>
                        </div>
                        {node.tools_called != null && node.tools_called.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {node.tools_called.map((tool) => (
                              <span
                                key={tool}
                                className="rounded-full border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] px-2 py-0.5 text-[10px] text-[color:var(--color-text-secondary)]"
                              >
                                {tool}
                              </span>
                            ))}
                          </div>
                        )}
                        {!isNotCalled && (
                          <p className="mt-2 text-xs text-[color:var(--color-text-secondary)] whitespace-pre-wrap break-words">
                            {node.output_preview?.trim() ? node.output_preview : t('chat.debug.no_output')}
                          </p>
                        )}
                      </div>
                    );
                  })}
                  {traceNodes.length === 0 && (
                    <p className="text-xs text-[color:var(--color-text-secondary)]">
                      {t('chat.debug.no_data')}
                    </p>
                  )}
                </div>
              </div>

            </div>
          )}
        </section>
      )}
    </div>
  );
}
