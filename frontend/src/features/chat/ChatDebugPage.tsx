import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { useChatStore } from '../../shared/hooks/useChat';
import type { ChatGraphTrace } from '../../shared/types/chat';

import { ChatDebugInspector } from './components/debug/ChatDebugInspector';
import { useChatDebugInspectorState } from './components/debug/useChatDebugInspectorState';

export default function ChatDebugPage() {
  const { turnId } = useParams<{ turnId: string }>();
  const navigate = useNavigate();
  const fetchDebugTrace = useChatStore((s) => s.fetchDebugTrace);
  const globalDebugTrace = useChatStore((s) => s.debugTrace);
  const globalDebugTraceError = useChatStore((s) => s.debugTraceError);
  const isStreaming = useChatStore((s) => s.isStreaming);

  const [localTrace, setLocalTrace] = useState<ChatGraphTrace | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fetchedRef = useRef(false);

  const inspectorState = useChatDebugInspectorState();

  const isDev = import.meta.env.DEV;

  useEffect(() => {
    if (!isDev || !turnId || fetchedRef.current) return;
    fetchedRef.current = true;

    const load = async () => {
      setLoading(true);
      try {
        await fetchDebugTrace(turnId);
      } catch {
        setLocalError('Failed to load trace');
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [turnId, fetchDebugTrace, isDev]);

  useEffect(() => {
    if (globalDebugTrace && globalDebugTrace.turn_id === turnId) {
      setLocalTrace(globalDebugTrace);
      setLocalError(null);
    }
  }, [globalDebugTrace, turnId]);

  useEffect(() => {
    if (globalDebugTraceError && !localTrace) {
      setLocalError(globalDebugTraceError);
    }
  }, [globalDebugTraceError, localTrace]);

  if (!isDev) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-[color:var(--color-text-secondary)]">Debug inspector unavailable outside development mode.</p>
      </div>
    );
  }

  if (loading && !localTrace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-[color:var(--color-text-secondary)]">Loading trace...</p>
      </div>
    );
  }

  if (localError && !localTrace) {
    return (
      <div className="flex items-center justify-center h-full flex-col gap-4">
        <p className="text-sm text-[color:var(--color-error)]">{localError}</p>
        <button
          type="button"
          onClick={() => { navigate('/dashboard/chat'); }}
          className="rounded-full border border-[color:var(--color-outline-variant)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
        >
          Back to chat
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-[color:var(--color-background)]">
      <div className="flex items-center justify-between px-4 py-2 border-b border-[color:var(--color-outline-variant)]">
        <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
          Debug Inspector - {turnId}
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => { void navigator.clipboard.writeText(JSON.stringify(localTrace ?? globalDebugTrace, null, 2)); }}
            className="rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
          >
            Copy trace
          </button>
          <button
            type="button"
            onClick={() => { navigate('/dashboard/chat'); }}
            className="rounded-full border border-[color:var(--color-outline-variant)] px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[color:var(--color-text-muted)] hover:text-[color:var(--color-text-primary)]"
          >
            Back
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0 p-4">
        <ChatDebugInspector
          debugTrace={localTrace ?? globalDebugTrace}
          debugTraceError={localError ?? globalDebugTraceError}
          isStreaming={isStreaming}
          expandedNode={inspectorState.expandedNode}
          showRawTrace={inspectorState.showRawTrace}
          activeTab={inspectorState.activeTab}
          onToggleNode={inspectorState.toggleNode}
          onToggleRawTrace={inspectorState.toggleRawTrace}
          onTabChange={inspectorState.setActiveTab}
        />
      </div>
    </div>
  );
}
