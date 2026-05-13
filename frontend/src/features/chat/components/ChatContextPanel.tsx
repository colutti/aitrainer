import { useTranslation } from 'react-i18next';

import type { ChatGraphTrace } from '../../../shared/types/chat';

import { ChatDebugInspector } from './debug/ChatDebugInspector';
import { useChatDebugInspectorState } from './debug/useChatDebugInspectorState';

interface ChatContextPanelProps {
  trainerName: string;
  trainerId: string | null;
  isStreaming: boolean;
  messageCount: number;
  debugTrace?: ChatGraphTrace | null;
  debugTraceError?: string | null;
  showDebugPanel?: boolean;
  onMaximize?: () => void;
}

export function ChatContextPanel({
  trainerName: _trainerName,
  trainerId: _trainerId,
  isStreaming,
  messageCount: _messageCount,
  debugTrace,
  debugTraceError,
  showDebugPanel = false,
  onMaximize,
}: ChatContextPanelProps) {
  const { t } = useTranslation();
  const {
    expandedNode,
    showRawTrace,
    activeTab,
    toggleNode,
    toggleRawTrace,
    setActiveTab,
  } = useChatDebugInspectorState();

  const sidebarWidth = 352;

  return (
    <div
      className="surface-card relative isolate flex h-full min-h-0 flex-col overflow-hidden"
      data-testid="chat-context-panel"
      style={{ width: `${sidebarWidth.toString()}px`, minWidth: `${sidebarWidth.toString()}px` }}
    >
      {showDebugPanel && (
        <>
          <div className="flex items-center justify-end gap-2 p-2 border-b border-[color:var(--color-outline-variant)]">
            {debugTrace?.turn_id && (
              <button
                type="button"
                onClick={() => {
                  window.open(`/dashboard/chat/debug/${debugTrace.turn_id}`, '_blank');
                }}
                className="rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
              >
                {t('chat.debug.open_full')}
              </button>
            )}
            {onMaximize && (
              <button
                type="button"
                onClick={onMaximize}
                className="rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
              >
                {t('chat.debug.maximize')}
              </button>
            )}
          </div>
          <ChatDebugInspector
            debugTrace={debugTrace}
            debugTraceError={debugTraceError}
            isStreaming={isStreaming}
            expandedNode={expandedNode}
            showRawTrace={showRawTrace}
            activeTab={activeTab}
            onToggleNode={toggleNode}
            onToggleRawTrace={toggleRawTrace}
            onTabChange={setActiveTab}
          />
        </>
      )}
    </div>
  );
}
