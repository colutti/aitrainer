import { httpClient } from '../../../shared/api/http-client';
import type { 
  WeightLog, 
  BodyCompositionStats,
  WeightListResponse
} from '../../../shared/types/body';
import type { ImportResult } from '../../../shared/types/import-result';
import type {
  MetabolismResponse
} from '../../../shared/types/metabolism';
import type {
  NutritionLog,
  NutritionStats,
  NutritionListResponse
} from '../../../shared/types/nutrition';

/**
 * API client for Body and Health related endpoints
 */
export const bodyApi = {
  // Weight & Body Composition
  getWeightHistory: async (page = 1, pageSize = 10): Promise<WeightListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    const result = await httpClient<WeightListResponse>(`/weight?${params.toString()}`);
    return result ?? {
      logs: [],
      total: 0,
      page: 1,
      page_size: 10,
      total_pages: 0
    };
  },
  
  getBodyCompositionStats: async (): Promise<BodyCompositionStats> => {
    const result = await httpClient<BodyCompositionStats>('/weight/stats');
    return result ?? {
      latest: null,
      weight_trend: [],
      fat_trend: [],
      muscle_trend: []
    };
  },
  
  logWeight: async (weight: number, data: Partial<WeightLog> = {}): Promise<WeightLog> => {
    return httpClient<WeightLog>('/weight', {
      method: 'POST',
      body: JSON.stringify({ weight_kg: weight, ...data }),
    }) as Promise<WeightLog>;
  },
  
  deleteWeight: async (date: string): Promise<void> => {
    await httpClient(`/weight/${date}`, { method: 'DELETE' });
  },

  // Nutrition
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
  
  getNutritionStats: async (): Promise<NutritionStats> => {
    return httpClient<NutritionStats>('/nutrition/stats') as Promise<NutritionStats>;
  },
  
  logNutrition: async (data: Partial<NutritionLog>): Promise<NutritionLog> => {
    return httpClient<NutritionLog>('/nutrition/log', {
      method: 'POST',
      body: JSON.stringify(data),
    }) as Promise<NutritionLog>;
  },
  
  deleteNutritionLog: async (id: string): Promise<void> => {
    await httpClient(`/nutrition/${id}`, { method: 'DELETE' });
  },

  // Metabolism
  getMetabolismSummary: async (weeks = 3): Promise<MetabolismResponse> => {
    return httpClient<MetabolismResponse>(`/metabolism/summary?weeks=${weeks.toString()}`) as Promise<MetabolismResponse>;
  },
  
  getMetabolismDefault: async (): Promise<MetabolismResponse> => {
    return httpClient<MetabolismResponse>('/metabolism/default') as Promise<MetabolismResponse>;
  },

  // Import
  importZeppLife: async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/integrations/zepp_life/import', {
      method: 'POST',
      headers: {
         ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: formData
    });
    
    if (!response.ok) {
        throw new Error('Falha no upload');
    }
    return response.json() as Promise<ImportResult>;
  }
};
