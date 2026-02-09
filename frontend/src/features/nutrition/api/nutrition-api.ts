import { httpClient } from '../../../shared/api/http-client';
import type {
  NutritionLog,
  NutritionStats,
  NutritionListResponse,
  CreateNutritionLogRequest
} from '../../../shared/types/nutrition';

/**
 * API client for Nutrition endpoints (standalone page)
 */
export const nutritionApi = {
  /**
   * Fetch paginated nutrition logs
   * @param page - Page number (1-indexed)
   * @param pageSize - Number of logs per page
   * @param days - Filter by recent days (optional)
   * @returns Paginated nutrition logs
   */
  getNutritionLogs: async (page = 1, pageSize = 10, days?: number): Promise<NutritionListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (days) params.append('days', days.toString());
    
    const result = await httpClient<NutritionListResponse>(`/nutrition/list?${params.toString()}`);
    return result ?? {
      logs: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0
    };
  },

  /**
   * Get nutrition statistics
   * @returns Nutrition stats including averages and trends
   */
  getNutritionStats: async (): Promise<NutritionStats> => {
    return httpClient<NutritionStats>('/nutrition/stats') as Promise<NutritionStats>;
  },

  /**
   * Log new nutrition entry
   * @param data - Nutrition log data
   * @returns Created nutrition log
   */
  logNutrition: async (data: CreateNutritionLogRequest): Promise<NutritionLog> => {
    return httpClient<NutritionLog>('/nutrition/log', {
      method: 'POST',
      body: JSON.stringify(data),
    }) as Promise<NutritionLog>;
  },

  /**
   * Delete nutrition log by ID
   * @param id - Nutrition log ID
   */
  deleteNutritionLog: async (id: string): Promise<void> => {
    await httpClient(`/nutrition/${id}`, { method: 'DELETE' });
  },
};
