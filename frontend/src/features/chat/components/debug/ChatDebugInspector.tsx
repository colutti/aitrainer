import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { ChatGraphNodeTrace, ChatGraphTrace, ChatGraphTraceTimelineSummary } from '../../../../shared/types/chat';
import { cn } from '../../../../shared/utils/cn';

const formatDuration = (durationMs?: number | null): string => {
  if (typeof durationMs !== 'number' || Number.isNaN(durationMs)) {
    return '--';
  }
  if (durationMs < 1000) {
    return `${durationMs}ms`;
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

function formatDebugValue(value: unknown): string {
  if (value === null || value === undefined) return '';
  if (typeof value === 'object' && !Array.isArray(value)) {
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return '[complex object]';
    }
  }
  if (typeof value === 'string') return value;
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return String(value);
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return '[complex value]';
  }
}

function JsonBlock({ data, label }: { data: unknown; label?: string }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const text = formatDebugValue(data);
  const isLarge = text.length > 200;
  const displayText = isLarge && !expanded ? text.slice(0, 200) + '...' : text;

  return (
    <div className="space-y-1">
      {label && (
        <p className="text-[10px] uppercase tracking-[0.14em] text-[color:var(--color-text-muted)]">{label}</p>
      )}
      <pre className="overflow-x-auto rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] p-2 text-[11px] leading-relaxed text-[color:var(--color-text-secondary)] font-mono whitespace-pre-wrap break-all">
        {displayText || '\u2014'}
      </pre>
      {isLarge && (
        <button
          type="button"
          className="text-[10px] text-[color:var(--color-primary)] hover:underline"
          onClick={() => { setExpanded(!expanded); }}
        >
          {expanded ? t('chat.debug.collapse') : t('chat.debug.expand')}
        </button>
      )}
    </div>
  );
}

function StateDiffBlock({ diff }: { diff: Record<string, unknown> | null | undefined }) {
  const { t } = useTranslation();
  if (!diff) return <p className="text-xs text-[color:var(--color-text-secondary)]">{t('chat.debug.no_diff')}</p>;

  const sections: { key: string; title: string; color: string }[] = [
    { key: 'added', title: t('chat.debug.diff_added'), color: 'text-emerald-400' },
    { key: 'changed', title: t('chat.debug.diff_changed'), color: 'text-amber-400' },
    { key: 'removed', title: t('chat.debug.diff_removed'), color: 'text-red-400' },
  ];

  return (
    <div className="space-y-2">
      {sections.map(({ key, title, color }) => {
        const items = diff[key] as Record<string, unknown> | undefined;
        if (!items || Object.keys(items).length === 0) return null;
        return (
          <div key={key}>
            <p className={cn('text-[10px] uppercase tracking-[0.14em]', color)}>
              {title} ({Object.keys(items).length})
            </p>
            <div className="mt-1 space-y-1">
              {Object.entries(items).map(([k, v]) => (
                <div key={k} className="rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] p-2">
                  <p className="text-[11px] font-mono text-[color:var(--color-text-primary)]">{k}</p>
                  <JsonBlock data={v} />
                </div>
              ))}
            </div>
          </div>
        );
      })}
      {sections.every(({ key }) => {
        const items = diff[key] as Record<string, unknown> | undefined;
        return !items || Object.keys(items).length === 0;
      }) && (
        <p className="text-xs text-[color:var(--color-text-secondary)]">{t('chat.debug.no_changes')}</p>
      )}
    </div>
  );
}

function TimelineBadge({ summary }: { summary?: ChatGraphTraceTimelineSummary | null }) {
  if (!summary) return null;
  const badges: string[] = [];
  if (summary.interrupted_at) badges.push(`interrupted@${summary.interrupted_at}`);
  if (summary.nodes_with_state_changes?.length) badges.push(`states:${summary.nodes_with_state_changes.length}`);
  if (summary.nodes_with_pending_actions?.length) badges.push(`pending:${summary.nodes_with_pending_actions.length}`);
  if (badges.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1">
      {badges.map((b) => (
        <span
          key={b}
          className="rounded-full border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] px-2 py-0.5 text-[10px] text-[color:var(--color-text-secondary)]"
        >
          {b}
        </span>
      ))}
    </div>
  );
}

function NodeDetailTabs({ node, activeTab, onTabChange }: { node: ChatGraphNodeTrace; activeTab: string; onTabChange: (tab: string) => void }) {
  const { t } = useTranslation();

  const tabs = [
    { id: 'summary', label: t('chat.debug.tab_summary') },
    { id: 'input', label: t('chat.debug.tab_input') },
    { id: 'output', label: t('chat.debug.tab_output') },
    { id: 'diff', label: t('chat.debug.tab_diff') },
    { id: 'config', label: t('chat.debug.tab_config') },
  ];

  return (
    <div className="mt-2">
      <div className="flex gap-1 border-b border-[color:var(--color-outline-variant)] pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => { onTabChange(tab.id); }}
            className={cn(
              'px-2 py-1 text-[10px] uppercase tracking-[0.12em] rounded-t-lg transition-colors',
              activeTab === tab.id
                ? 'bg-[color:var(--color-surface-container)] text-[color:var(--color-text-primary)] font-semibold'
                : 'text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-secondary)]',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-2 space-y-2">
        {activeTab === 'summary' && <NodeSummary node={node} />}
        {activeTab === 'input' && <NodeInput node={node} />}
        {activeTab === 'output' && <NodeOutput node={node} />}
        {activeTab === 'diff' && <StateDiffBlock diff={node.state_diff} />}
        {activeTab === 'config' && <NodeConfig node={node} />}
      </div>
    </div>
  );
}

function NodeSummary({ node }: { node: ChatGraphNodeTrace }) {
  const { t } = useTranslation();
  return (
    <div className="grid grid-cols-2 gap-2 text-[11px]">
      <div><span className="text-[color:var(--color-text-muted)]">{t('chat.debug.status_label')}:</span> <span className="text-[color:var(--color-text-primary)]">{node.status}</span></div>
      <div><span className="text-[color:var(--color-text-muted)]">{t('chat.debug.duration')}:</span> <span className="text-[color:var(--color-text-primary)]">{formatDuration(node.duration_ms)}</span></div>
      <div><span className="text-[color:var(--color-text-muted)]">{t('chat.debug.model')}:</span> <span className="text-[color:var(--color-text-primary)] font-mono text-[10px]">{node.model ?? '\u2014'}</span></div>
      <div><span className="text-[color:var(--color-text-muted)]">{t('chat.debug.config_version')}:</span> <span className="text-[color:var(--color-text-primary)]">{node.config_version ?? '\u2014'}</span></div>
      {node.error && (
        <div className="col-span-2 rounded-xl border border-red-500/20 bg-red-500/10 p-2">
          <p className="text-[color:var(--color-error)]">{node.error}</p>
        </div>
      )}
      {node.specialist_state && Object.keys(node.specialist_state).length > 0 && (
        <div className="col-span-2">
          <JsonBlock data={node.specialist_state} label={t('chat.debug.specialist_state')} />
        </div>
      )}
      {node.pending_action && Object.keys(node.pending_action).length > 0 && (
        <div className="col-span-2">
          <JsonBlock data={node.pending_action} label={t('chat.debug.pending_action')} />
        </div>
      )}
      {node.tools_called && node.tools_called.length > 0 && (
        <div className="col-span-2 flex flex-wrap gap-1">
          {node.tools_called.map((tool) => (
            <span key={tool} className="rounded-full border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] px-2 py-0.5 text-[10px] text-[color:var(--color-text-secondary)]">{tool}</span>
          ))}
        </div>
      )}
    </div>
  );
}

function NodeInput({ node }: { node: ChatGraphNodeTrace }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-2">
      <JsonBlock data={node.resolved_input} label={t('chat.debug.resolved_input')} />
      <JsonBlock data={node.resolved_context} label={t('chat.debug.resolved_context')} />
      <JsonBlock data={node.resolved_peer_outputs} label={t('chat.debug.resolved_peer_outputs')} />
    </div>
  );
}

function NodeOutput({ node }: { node: ChatGraphNodeTrace }) {
  const { t } = useTranslation();
  return (
    <div className="space-y-2">
      <JsonBlock data={node.output_preview} label={t('chat.debug.output_preview')} />
      <JsonBlock data={node.raw_output} label={t('chat.debug.raw_output')} />
      {node.structured_output && (
        <JsonBlock data={node.structured_output} label={t('chat.debug.structured_output')} />
      )}
    </div>
  );
}

function NodeConfig({ node }: { node: ChatGraphNodeTrace }) {
  const { t } = useTranslation();
  const configItems: { key: keyof ChatGraphNodeTrace; label: string }[] = [
    { key: 'model', label: t('chat.debug.model') },
    { key: 'config_version', label: t('chat.debug.config_version') },
    { key: 'config_hash', label: t('chat.debug.config_hash') },
    { key: 'temperature', label: t('chat.debug.temperature') },
    { key: 'max_tokens', label: t('chat.debug.max_tokens') },
    { key: 'top_p', label: t('chat.debug.top_p') },
    { key: 'frequency_penalty', label: t('chat.debug.frequency_penalty') },
    { key: 'provider_sort', label: t('chat.debug.provider_sort') },
    { key: 'tool_policy', label: t('chat.debug.tool_policy') },
  ];

  return (
    <div className="space-y-1">
      {configItems.map(({ key, label }) => {
        const value = node[key];
        const displayValue = typeof value === 'object' && value !== null
          ? JSON.stringify(value)
          : value != null
            ? String(value)
            : '\u2014';
        return (
          <div key={key} className="grid grid-cols-2 gap-2 text-[11px]">
            <span className="text-[color:var(--color-text-muted)]">{label}</span>
            <span className="text-[color:var(--color-text-primary)] font-mono text-[10px] break-all">{displayValue}</span>
          </div>
        );
      })}
      <JsonBlock data={node.context_blocks} label={t('chat.debug.context_blocks')} />
      <JsonBlock data={node.peer_inputs} label={t('chat.debug.peer_inputs')} />
      <JsonBlock data={node.reasoning} label={t('chat.debug.reasoning')} />
    </div>
  );
}

export interface ChatDebugInspectorProps {
  debugTrace: ChatGraphTrace | null | undefined;
  debugTraceError?: string | null;
  isStreaming: boolean;
  expandedNode: string | null;
  showRawTrace: boolean;
  activeTab: string;
  onToggleNode: (name: string) => void;
  onToggleRawTrace: () => void;
  onTabChange: (tab: string) => void;
}

export function ChatDebugInspector({
  debugTrace,
  debugTraceError,
  isStreaming,
  expandedNode,
  showRawTrace,
  activeTab,
  onToggleNode,
  onToggleRawTrace,
  onTabChange,
}: ChatDebugInspectorProps) {
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
    <section className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
            {t('chat.debug.title')}
          </p>
        </div>
        {debugTrace && (
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onToggleRawTrace}
              className={cn(
                'rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] transition-colors',
                showRawTrace
                  ? 'border-[color:var(--color-primary)]/30 bg-[color:var(--color-primary)]/10 text-[color:var(--color-primary)]'
                  : 'border-[color:var(--color-outline-variant)] text-[color:var(--color-text-muted)]',
              )}
            >
              raw
            </button>
            <span className={cn(
              'rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]',
              debugTrace.status === 'success'
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                : 'border-amber-500/30 bg-amber-500/10 text-amber-300',
            )}>
              {nodeStatuses[debugTrace.status] ?? debugTrace.status}
            </span>
          </div>
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
      ) : showRawTrace ? (
        <div className="mt-4 flex min-h-0 flex-1 flex-col">
          <button
            type="button"
            onClick={() => { void navigator.clipboard.writeText(JSON.stringify(debugTrace, null, 2)); }}
            className="self-end mb-2 rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
          >
            {t('chat.debug.copy_trace')}
          </button>
          <pre className="flex-1 overflow-auto rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] p-3 text-[11px] leading-relaxed text-[color:var(--color-text-secondary)] font-mono whitespace-pre-wrap break-all">
            {JSON.stringify(debugTrace, null, 2)}
          </pre>
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
            {debugTrace.graph_error && (
              <div className="col-span-2">
                <dt className="text-[color:var(--color-text-muted)] uppercase tracking-[0.14em]">{t('chat.debug.graph_error')}</dt>
                <dd className="mt-1 text-xs text-[color:var(--color-error)]">{debugTrace.graph_error}</dd>
              </div>
            )}
          </dl>

          {debugTrace.timeline_summary && (
            <TimelineBadge summary={debugTrace.timeline_summary} />
          )}

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
                const isExpanded = expandedNode === node.node_name;
                return (
                  <div key={node.node_name}>
                    <button
                      type="button"
                      onClick={() => { onToggleNode(node.node_name); }}
                      className={cn(
                        'w-full cursor-pointer rounded-2xl border p-3 text-left transition-colors',
                        getNodeStatusClasses(node.status, hasStarted),
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-[color:var(--color-text-primary)]">{node.node_name}</p>
                          <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-[color:var(--color-text-muted)]">
                            {nodeStatuses[displayStatus] ?? displayStatus}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {node.duration_ms != null && (
                            <span className="text-[10px] font-mono text-[color:var(--color-text-muted)]">
                              {formatDuration(node.duration_ms)}
                            </span>
                          )}
                          <span className={cn('text-[10px] transition-transform', isExpanded ? 'rotate-180' : '')}>
                            {'\u25BC'}
                          </span>
                        </div>
                      </div>
                      {!isNotCalled && !isExpanded && node.output_preview?.trim() && (
                        <p className="mt-2 text-xs text-[color:var(--color-text-secondary)] truncate">
                          {node.output_preview}
                        </p>
                      )}
                    </button>
                    {isExpanded && (
                      <NodeDetailTabs
                        node={node}
                        activeTab={activeTab}
                        onTabChange={onTabChange}
                      />
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
  );
}
