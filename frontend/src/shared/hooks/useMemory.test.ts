import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../api/http-client';

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

  const mockMemories = [
    { id: '1', content: 'Memory 1', importance: 1 } as any,
    { id: '2', content: 'Memory 2', importance: 2 } as any,
  ];

  it('should have initial state', () => {
    const state = useMemoryStore.getState();
    expect(state.memories).toEqual([]);
    expect(state.isLoading).toBe(false);
  });

  describe('fetchMemories', () => {
    it('should fetch memories successfully', async () => {
      const mockResponse = {
        memories: mockMemories,
        total: 2,
        page: 1,
        page_size: 10,
        total_pages: 1,
      };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);

      await useMemoryStore.getState().fetchMemories(1);

      const state = useMemoryStore.getState();
      expect(state.memories).toEqual(mockMemories);
      expect(state.totalMemories).toBe(2);
      expect(state.isLoading).toBe(false);
      expect(httpClient).toHaveBeenCalledWith('/memory/list?page=1&page_size=10');
    });

    it('should handle fetch memories error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(httpClient).mockRejectedValue(new Error('failed'));

      await useMemoryStore.getState().fetchMemories(1);

      const state = useMemoryStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe('Falha ao carregar memórias.');
      consoleSpy.mockRestore();
    });
  });

  describe('pagination', () => {
    it('should go to next page if available', async () => {
      useMemoryStore.setState({ currentPage: 1, totalPages: 2 });
      vi.mocked(httpClient).mockResolvedValue({ memories: [], total: 0, page: 2, total_pages: 2 });

      await useMemoryStore.getState().nextPage();

      expect(httpClient).toHaveBeenCalledWith('/memory/list?page=2&page_size=10');
    });

    it('should not go to next page if on last page', async () => {
      useMemoryStore.setState({ currentPage: 2, totalPages: 2 });
      await useMemoryStore.getState().nextPage();
      expect(httpClient).not.toHaveBeenCalled();
    });

    it('should go to previous page if available', async () => {
      useMemoryStore.setState({ currentPage: 2, totalPages: 2 });
      vi.mocked(httpClient).mockResolvedValue({ memories: [], total: 0, page: 1, total_pages: 2 });

      await useMemoryStore.getState().previousPage();

      expect(httpClient).toHaveBeenCalledWith('/memory/list?page=1&page_size=10');
    });

    it('should not go to previous page if on first page', async () => {
      useMemoryStore.setState({ currentPage: 1, totalPages: 2 });
      await useMemoryStore.getState().previousPage();
      expect(httpClient).not.toHaveBeenCalled();
    });
  });

  describe('deleteMemory', () => {
    it('should delete memory and refresh', async () => {
      vi.mocked(httpClient).mockResolvedValue({});
      // Mock subsequent fetch
      vi.mocked(httpClient)
        .mockResolvedValueOnce({}) // delete
        .mockResolvedValueOnce({ memories: [], total: 0, page: 1, total_pages: 0 }); // refresh

      await useMemoryStore.getState().deleteMemory('1');

      expect(httpClient).toHaveBeenCalledWith('/memory/1', { method: 'DELETE' });
      expect(httpClient).toHaveBeenCalledWith('/memory/list?page=1&page_size=10');
    });

    it('should handle delete error', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.mocked(httpClient).mockRejectedValue(new Error('failed'));

      await useMemoryStore.getState().deleteMemory('1');

      const state = useMemoryStore.getState();
      expect(state.error).toBe('Falha ao excluir memória.');
      expect(state.isLoading).toBe(false);
      consoleSpy.mockRestore();
    });
  });
});
