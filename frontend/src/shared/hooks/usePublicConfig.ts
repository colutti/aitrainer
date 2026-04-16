import { useEffect } from 'react';
import { create } from 'zustand';

import { httpClient } from '../api/http-client';

interface PublicConfigResponse {
  enable_new_user_signups?: boolean;
}

interface PublicConfigState {
  enableNewUserSignups: boolean;
  isLoading: boolean;
  hasLoaded: boolean;
  load: () => Promise<void>;
}

export const usePublicConfigStore = create<PublicConfigState>((set, get) => ({
  enableNewUserSignups: false,
  isLoading: false,
  hasLoaded: false,
  load: async () => {
    if (get().isLoading || get().hasLoaded) {
      return;
    }

    set({ isLoading: true });
    try {
      const data = await httpClient<PublicConfigResponse>('/user/public-config');
      set({
        enableNewUserSignups: data?.enable_new_user_signups === true,
        isLoading: false,
        hasLoaded: true,
      });
    } catch {
      set({
        enableNewUserSignups: false,
        isLoading: false,
        hasLoaded: true,
      });
    }
  },
}));

export function usePublicConfig() {
  const enableNewUserSignups = usePublicConfigStore((state) => state.enableNewUserSignups);
  const isLoading = usePublicConfigStore((state) => state.isLoading);
  const hasLoaded = usePublicConfigStore((state) => state.hasLoaded);
  const load = usePublicConfigStore((state) => state.load);

  useEffect(() => {
    if (!hasLoaded && !isLoading) {
      void load();
    }
  }, [hasLoaded, isLoading, load]);

  return {
    enableNewUserSignups,
    isLoading,
    hasLoaded,
  };
}
