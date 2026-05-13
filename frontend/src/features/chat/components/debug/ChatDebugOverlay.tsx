import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import type { ChatGraphTrace } from '../../../../shared/types/chat';

import { ChatDebugInspector } from './ChatDebugInspector';

interface ChatDebugOverlayProps {
  open: boolean;
  onClose: () => void;
  debugTrace: ChatGraphTrace | null | undefined;
  debugTraceError?: string | null;
  isStreaming: boolean;
  expandedNode: string | null;
  showRawTrace: boolean;
  activeTab: string;
  onToggleNode: (name: string) => void;
  onToggleRawTrace: () => void;
  onTabChange: (tab: string) => void;
  turnId?: string;
}

export function ChatDebugOverlay({
  open,
  onClose,
  debugTrace,
  debugTraceError,
  isStreaming,
  expandedNode,
  showRawTrace,
  activeTab,
  onToggleNode,
  onToggleRawTrace,
  onTabChange,
  turnId,
}: ChatDebugOverlayProps) {
  const { t } = useTranslation();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) {
      document.addEventListener('keydown', handler);
      return () => document.removeEventListener('keydown', handler);
    }
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-[color:var(--color-background)]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[color:var(--color-outline-variant)]">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
          {t('chat.debug.title')}
        </p>
        <div className="flex items-center gap-2">
          {turnId && (
            <button
              type="button"
              onClick={() => { window.open(`/dashboard/chat/debug/${turnId}`, '_blank'); }}
              className="rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
            >
              {t('chat.debug.open_full')}
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
          >
            {t('chat.debug.close')}
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0 p-4">
        <ChatDebugInspector
          debugTrace={debugTrace}
          debugTraceError={debugTraceError}
          isStreaming={isStreaming}
          expandedNode={expandedNode}
          showRawTrace={showRawTrace}
          activeTab={activeTab}
          onToggleNode={onToggleNode}
          onToggleRawTrace={onToggleRawTrace}
          onTabChange={onTabChange}
        />
      </div>
    </div>
  );
}
