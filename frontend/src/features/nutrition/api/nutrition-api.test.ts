import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { nutritionApi } from './nutrition-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('nutritionApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch paginated nutrition logs', async () => {
    const mockResponse = {
      logs: [{ id: '1', date: '2024-01-01', calories: 2000 }],
      total: 100,
      page: 1,
      page_size: 10,
      total_pages: 10
    };
    vi.mocked(httpClient).mockResolvedValue(mockResponse);
    
    const res = await nutritionApi.getNutritionLogs(1, 10, 7);
    expect(res).toEqual(mockResponse);
    expect(httpClient).toHaveBeenCalledWith('/nutrition/list?page=1&page_size=10&days=7');
  });

  it('should fetch nutrition stats', async () => {
    const mockStats = { avg_daily_calories: 2200, total_logs: 50 };
    vi.mocked(httpClient).mockResolvedValue(mockStats);
    
    await nutritionApi.getNutritionStats();
    expect(httpClient).toHaveBeenCalledWith('/nutrition/stats');
  });

  it('should log nutrition', async () => {
    const logData = { date: '2024-01-01', source: 'manual', calories: 2000, protein_grams: 150, carbs_grams: 200, fat_grams: 60 };
    vi.mocked(httpClient).mockResolvedValue({ id: '1', ...logData });
    
    await nutritionApi.logNutrition(logData);
    expect(httpClient).toHaveBeenCalledWith('/nutrition/log', {
      method: 'POST',
      body: JSON.stringify(logData),
    });
  });

  it('should delete nutrition log', async () => {
    await nutritionApi.deleteNutritionLog('123');
    expect(httpClient).toHaveBeenCalledWith('/nutrition/123', { method: 'DELETE' });
  });
});
