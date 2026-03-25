import { create } from 'zustand';

import { httpClient } from '../api/http-client';

interface EntityState<T> {
  items: T[];
  total: number;
  page: number;
  totalPages: number;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  
  // Actions
  fetchItems: (page?: number, limit?: number) => Promise<void>;
  deleteItem: (id: string) => Promise<void>;
  reset: () => void;
}

interface EntityStoreConfig {
  endpoint: string;
  itemsKey?: string;
}

interface GenericResponse {
  total?: number;
  page?: number;
  total_pages?: number;
  [key: string]: unknown;
}

/**
 * Factory function to create standardized Zustand stores for any entity.
 */
export function createEntityStore<T>(config: EntityStoreConfig) {
  const { endpoint, itemsKey = 'items' } = config;

  return create<EntityState<T>>((set, get) => ({
    items: [],
    total: 0,
    page: 1,
    totalPages: 0,
    isLoading: false,
    isSaving: false,
    error: null,

    fetchItems: async (page = 1, limit = 20) => {
      set({ isLoading: true, error: null });
      try {
        const response = await httpClient<GenericResponse>(`${endpoint}?page=${String(page)}&limit=${String(limit)}`);
        if (!response) throw new Error('Empty response');
        
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        const items = (response[itemsKey] as T[]) ?? [];
        set({
          items,
          total: response.total ?? 0,
          page: response.page ?? 1,
          totalPages: response.total_pages ?? 0,
          isLoading: false
        });

      } catch (err) {
        set({ 
          error: err instanceof Error ? err.message : 'Unknown error', 
          isLoading: false 
        });
        throw err;
      }
    },

    deleteItem: async (id: string) => {
      set({ isSaving: true, error: null });
      try {
        await httpClient(`${endpoint}/${id}`, { method: 'DELETE' });
        const { items, total } = get();
        set({
          items: items.filter((item) => {
            const itemId = (item as { id?: string; _id?: string }).id ?? (item as { id?: string; _id?: string })._id;
            return itemId !== id;
          }),
          total: total - 1,
          isSaving: false
        });
      } catch (err) {
        set({ 
          error: err instanceof Error ? err.message : 'Unknown error', 
          isSaving: false 
        });
        throw err;
      }
    },

    reset: () => {
      set({
        items: [],
        total: 0,
        page: 1,
        totalPages: 0,
        isLoading: false,
        isSaving: false,
        error: null
      });
    }
  }));
}
