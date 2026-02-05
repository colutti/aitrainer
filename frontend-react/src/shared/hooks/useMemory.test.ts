import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';
import type { MemoryListResponse } from '../types/memory';

import { useMemoryStore } from './useMemory';

// Mock httpClient
vi.mock('../api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('useMemoryStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useMemoryStore.getState().reset();
  });

  it('should have initial state', () => {
    const state = useMemoryStore.getState();
    expect(state.memories).toEqual([]);
    expect(state.isLoading).toBe(false);
    expect(state.currentPage).toBe(1);
  });

  it('should fetch memories successfully', async () => {
    const mockResponse: MemoryListResponse = {
      memories: [{ id: '1', memory: 'Likes apples', created_at: '2024-01-01', updated_at: '2024-01-01' }],
      total: 1,
      page: 1,
      page_size: 10,
      total_pages: 1,
    };

    vi.mocked(httpClient).mockResolvedValue(mockResponse);

    await useMemoryStore.getState().fetchMemories();

    const state = useMemoryStore.getState();
    expect(state.memories).toEqual(mockResponse.memories);
    expect(state.totalMemories).toBe(1);
    expect(httpClient).toHaveBeenCalledWith('/memory/list?page=1&page_size=10');
  });

  it('should handle delete memory', async () => {
    const mockResponse = {
      memories: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0,
    };

    vi.mocked(httpClient).mockResolvedValueOnce({ message: 'Deleted' });
    vi.mocked(httpClient).mockResolvedValueOnce(mockResponse);

    await useMemoryStore.getState().deleteMemory('1');

    expect(httpClient).toHaveBeenCalledWith('/memory/1', { method: 'DELETE' });
    expect(httpClient).toHaveBeenCalledWith('/memory/list?page=1&page_size=10');
  });
});
