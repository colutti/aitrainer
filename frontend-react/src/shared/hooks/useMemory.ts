import { create } from 'zustand';

import { httpClient } from '../api/http-client';
import type { Memory, MemoryListResponse } from '../types/memory';

interface MemoryState {
  memories: Memory[];
  isLoading: boolean;
  currentPage: number;
  pageSize: number;
  totalPages: number;
  totalMemories: number;
  error: string | null;
}

interface MemoryActions {
  fetchMemories: (page?: number) => Promise<void>;
  nextPage: () => Promise<void>;
  previousPage: () => Promise<void>;
  deleteMemory: (memoryId: string) => Promise<void>;
  reset: () => void;
}

type MemoryStore = MemoryState & MemoryActions;

/**
 * Memory store using Zustand
 * 
 * Manages paginated user memories stored in the AI brain.
 */
export const useMemoryStore = create<MemoryStore>((set, get) => ({
  memories: [],
  isLoading: false,
  currentPage: 1,
  pageSize: 10,
  totalPages: 0,
  totalMemories: 0,
  error: null,

  fetchMemories: async (page = get().currentPage) => {
    set({ isLoading: true, error: null });
    try {
      const response = await httpClient<MemoryListResponse>(
        `/memory/list?page=${page.toString()}&page_size=${get().pageSize.toString()}`
      );

      if (response) {
        set({
          memories: response.memories,
          currentPage: response.page,
          totalPages: response.total_pages,
          totalMemories: response.total,
          isLoading: false,
        });
      } else {
        set({ memories: [], isLoading: false });
      }
    } catch (error) {
      console.error('Error fetching memories:', error);
      set({ isLoading: false, error: 'Falha ao carregar memórias.' });
    }
  },

  nextPage: async () => {
    const { currentPage, totalPages } = get();
    if (currentPage < totalPages) {
      await get().fetchMemories(currentPage + 1);
    }
  },

  previousPage: async () => {
    const { currentPage } = get();
    if (currentPage > 1) {
      await get().fetchMemories(currentPage - 1);
    }
  },

  deleteMemory: async (memoryId: string) => {
    set({ isLoading: true });
    try {
      await httpClient(`/memory/${memoryId}`, { method: 'DELETE' });
      await get().fetchMemories(get().currentPage);
    } catch (error) {
      console.error('Error deleting memory:', error);
      set({ isLoading: false, error: 'Falha ao excluir memória.' });
    }
  },

  reset: () => {
    set({
      memories: [],
      isLoading: false,
      currentPage: 1,
      pageSize: 10,
      totalPages: 0,
      totalMemories: 0,
      error: null,
    });
  },
}));
