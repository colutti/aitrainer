import { useState, useCallback, useEffect } from 'react';

import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { MetabolismResponse } from '../../../shared/types/metabolism';
import { bodyApi } from '../api/body-api';

/**
 * Hook to manage Metabolism Tab state and logic
 */
export function useMetabolismTab() {
  const [stats, setStats] = useState<MetabolismResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [weeks, setWeeks] = useState(3);
  const notify = useNotificationStore();

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await bodyApi.getMetabolismSummary(weeks);
      setStats(data);
    } catch {
      notify.error('Erro ao carregar dados metabólicos.');
    } finally {
      setIsLoading(false);
    }
  }, [weeks, notify]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  return {
    stats,
    isLoading,
    weeks,
    loadData,
    setWeeks
  };
}
