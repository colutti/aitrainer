import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { memoriesApi } from './memories-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('memoriesApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getMemories', () => {
    it('should call httpClient with correct params', async () => {
      const mockResponse = { memories: [], total: 0, page: 1, page_size: 20, total_pages: 0 };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);

      const result = await memoriesApi.getMemories(2, 10, 'test');

      expect(httpClient).toHaveBeenCalledWith('/memory/list?page=2&page_size=10&search=test');
      expect(result).toEqual(mockResponse);
    });

    it('should return default object if httpClient returns null', async () => {
      vi.mocked(httpClient).mockResolvedValue(null);

      const result = await memoriesApi.getMemories();

      expect(result.memories).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('deleteMemory', () => {
    it('should call httpClient with DELETE method', async () => {
      vi.mocked(httpClient).mockResolvedValue({});

      await memoriesApi.deleteMemory('123');

      expect(httpClient).toHaveBeenCalledWith('/memory/123', { method: 'DELETE' });
    });
  });
});
