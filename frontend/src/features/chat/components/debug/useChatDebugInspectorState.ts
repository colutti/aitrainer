import { useState, useCallback } from 'react';

const STORAGE_PREFIX = 'chat_debug_';

function getPersistedValue<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + key);
    if (raw === null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function persistValue(key: string, value: unknown) {
  try {
    localStorage.setItem(STORAGE_PREFIX + key, JSON.stringify(value));
  } catch {
    // localStorage may be full or unavailable
  }
}

export function useChatDebugInspectorState() {
  const [expandedNode, setExpandedNodeState] = useState<string | null>(
    () => getPersistedValue<string | null>('selected_node', null),
  );
  const [showRawTrace, setShowRawTraceState] = useState(
    () => getPersistedValue('raw_mode', false),
  );
  const [sidebarWidth, setSidebarWidthState] = useState(
    () => getPersistedValue('sidebar_width', 352),
  );
  const [showOverlay, setShowOverlay] = useState(false);
  const [activeTab, setActiveTabState] = useState(
    () => getPersistedValue('active_tab', 'summary'),
  );

  const setActiveTab = useCallback((tab: string) => {
    setActiveTabState(tab);
    persistValue('active_tab', tab);
  }, []);

  const setExpandedNode = useCallback((name: string | null) => {
    setExpandedNodeState(name);
    persistValue('selected_node', name);
  }, []);

  const setShowRawTrace = useCallback((v: boolean) => {
    setShowRawTraceState(v);
    persistValue('raw_mode', v);
  }, []);

  const setSidebarWidth = useCallback((w: number) => {
    setSidebarWidthState(w);
    persistValue('sidebar_width', w);
  }, []);

  const toggleNode = useCallback((name: string) => {
    setExpandedNodeState(prev => {
      const next = prev === name ? null : name;
      persistValue('selected_node', next);
      return next;
    });
  }, []);

  const toggleRawTrace = useCallback(() => {
    setShowRawTraceState(prev => {
      persistValue('raw_mode', !prev);
      return !prev;
    });
  }, []);

  return {
    expandedNode,
    showRawTrace,
    sidebarWidth,
    showOverlay,
    activeTab,
    setExpandedNode,
    setShowRawTrace,
    setSidebarWidth,
    setShowOverlay,
    setActiveTab,
    toggleNode,
    toggleRawTrace,
  };
}
