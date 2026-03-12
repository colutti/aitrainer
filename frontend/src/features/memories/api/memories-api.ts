import { httpClient } from '../../../shared/api/http-client';
import type { Memory } from '../../../shared/types/memory';

export interface MemoriesListResponse {
  memories: Memory[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * API client for Memories/Mem0 endpoints
 */
export const memoriesApi = {
  /**
   * Fetch paginated memories
   */
  getMemories: async (page = 1, pageSize = 20, search = ''): Promise<MemoriesListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) params.append('search', search);
    
    const result = await httpClient<MemoriesListResponse>(`/memory/list?${params.toString()}`);
    return result ?? {
      memories: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 0
    };
  },

  /**
   * Delete a memory by ID
   */
  deleteMemory: async (id: string): Promise<void> => {
    await httpClient(`/memory/${id}`, { method: 'DELETE' });
  },
};
