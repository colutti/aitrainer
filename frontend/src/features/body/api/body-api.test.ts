import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { bodyApi } from './body-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('bodyApi', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'mock-token'),
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.unstubAllGlobals();
  });

  describe('Weight', () => {
    it('should fetch weight history with default params', async () => {
      const mockResponse = { logs: [], total: 0, page: 1, page_size: 10, total_pages: 0 };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);
      
      const res = await bodyApi.getWeightHistory();
      expect(res).toEqual(mockResponse);
      const params = new URLSearchParams({ page: '1', page_size: '10' });
      expect(httpClient).toHaveBeenCalledWith(`/weight?${params.toString()}`);
    });

    it('should fetch weight history with custom params', async () => {
      const mockResponse = { logs: [], total: 0, page: 2, page_size: 20, total_pages: 0 };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);
      
      const res = await bodyApi.getWeightHistory(2, 20);
      expect(res).toEqual(mockResponse);
      const params = new URLSearchParams({ page: '2', page_size: '20' });
      expect(httpClient).toHaveBeenCalledWith(`/weight?${params.toString()}`);
    });

    it('should return default structure when weight history returns null', async () => {
      vi.mocked(httpClient).mockResolvedValue(null);
      
      const res = await bodyApi.getWeightHistory();
      expect(res).toEqual({
        logs: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      });
    });

    it('should log weight', async () => {
      await bodyApi.logWeight(75.5, { date: '2024-01-02' });
      expect(httpClient).toHaveBeenCalledWith('/weight', {
        method: 'POST',
        body: JSON.stringify({ weight_kg: 75.5, date: '2024-01-02' }),
      });
    });

    it('should delete weight', async () => {
      await bodyApi.deleteWeight('2024-01-01');
      expect(httpClient).toHaveBeenCalledWith('/weight/2024-01-01', { method: 'DELETE' });
    });

    it('should get body composition stats', async () => {
      const mockStats = { latest: { weight_kg: 80 }, weight_trend: [] };
      vi.mocked(httpClient).mockResolvedValue(mockStats);
      
      const res = await bodyApi.getBodyCompositionStats();
      expect(res).toEqual(mockStats);
      expect(httpClient).toHaveBeenCalledWith('/weight/stats');
    });

    it('should return default stats when body composition returns null', async () => {
      vi.mocked(httpClient).mockResolvedValue(null);
      
      const res = await bodyApi.getBodyCompositionStats();
      expect(res).toEqual({
        latest: null,
        weight_trend: [],
        fat_trend: [],
        muscle_trend: []
      });
    });
  });

  describe('Nutrition', () => {
    it('should fetch nutrition logs with default params', async () => {
      const mockResponse = { logs: [], total: 0 };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);
      
      const res = await bodyApi.getNutritionLogs();
      const params = new URLSearchParams({ page: '1', page_size: '10' });
      expect(httpClient).toHaveBeenCalledWith(`/nutrition/list?${params.toString()}`);
      expect(res).toEqual(mockResponse);
    });

    it('should fetch nutrition logs with custom params and days', async () => {
      const mockResponse = { logs: [], total: 0 };
      vi.mocked(httpClient).mockResolvedValue(mockResponse);
      
      await bodyApi.getNutritionLogs(2, 20, 7);
      const params = new URLSearchParams({ page: '2', page_size: '20', days: '7' });
      expect(httpClient).toHaveBeenCalledWith(`/nutrition/list?${params.toString()}`);
    });

    it('should return default structure when nutrition logs returns null', async () => {
      vi.mocked(httpClient).mockResolvedValue(null);
      
      const res = await bodyApi.getNutritionLogs();
      expect(res).toEqual({
        logs: [],
        total: 0,
        page: 1,
        page_size: 10,
        total_pages: 0
      });
    });

    it('should fetch nutrition stats', async () => {
      const mockStats = { today_calories: 2000 };
      vi.mocked(httpClient).mockResolvedValue(mockStats);
      
      const res = await bodyApi.getNutritionStats();
      expect(res).toEqual(mockStats);
      expect(httpClient).toHaveBeenCalledWith('/nutrition/stats');
    });

    it('should log nutrition', async () => {
      const logData = { calories: 2000, protein_grams: 150 };
      await bodyApi.logNutrition(logData);
      expect(httpClient).toHaveBeenCalledWith('/nutrition/log', {
        method: 'POST',
        body: JSON.stringify(logData),
      });
    });

    it('should delete nutrition log', async () => {
      await bodyApi.deleteNutritionLog('log-123');
      expect(httpClient).toHaveBeenCalledWith('/nutrition/log-123', { method: 'DELETE' });
    });
  });

  describe('Metabolism', () => {
    it('should fetch metabolism summary with default weeks', async () => {
      await bodyApi.getMetabolismSummary();
      expect(httpClient).toHaveBeenCalledWith('/metabolism/summary?weeks=3');
    });

    it('should fetch metabolism summary with custom weeks', async () => {
      await bodyApi.getMetabolismSummary(4);
      expect(httpClient).toHaveBeenCalledWith('/metabolism/summary?weeks=4');
    });

    it('should fetch metabolism default', async () => {
      await bodyApi.getMetabolismDefault();
      expect(httpClient).toHaveBeenCalledWith('/metabolism/default');
    });
  });

  describe('Import', () => {
    it('should import Zepp Life CSV', async () => {
      const file = new File(['content'], 'test.csv', { type: 'text/csv' });
      const mockRes = { imported: 10 };
      
      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockRes)
      } as Response);

      const res = await bodyApi.importZeppLife(file);
      
      expect(res).toEqual(mockRes);
      expect(global.fetch).toHaveBeenCalledWith('/api/integrations/zepp_life/import', expect.objectContaining({
        method: 'POST',
        headers: { Authorization: 'Bearer mock-token' },
        body: expect.any(FormData)
      }));
    });

    it('should throw error on failed import', async () => {
      const file = new File(['content'], 'test.csv', { type: 'text/csv' });
      
      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 500
      } as Response);

      await expect(bodyApi.importZeppLife(file)).rejects.toThrow('Falha no upload');
    });
  });
});
