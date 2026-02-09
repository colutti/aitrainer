import { httpClient } from '../../../shared/api/http-client';
import type { HevyStatus, ImportResult } from '../../../shared/types/integration';

export const integrationsApi = {
  // Hevy
  getHevyStatus: async (): Promise<HevyStatus | undefined> => {
    return httpClient('/integrations/hevy/status');
  },
  
  saveHevyKey: async (apiKey: string): Promise<HevyStatus | undefined> => {
    return httpClient('/integrations/hevy/config', {
      method: 'POST',
      body: JSON.stringify({ api_key: apiKey })
    });
  },

  syncHevy: async (): Promise<{ message: string; workouts: number } | undefined> => {
    return httpClient('/integrations/hevy/sync', { method: 'POST' });
  },

  // MyFitnessPal (CSV Import)
  uploadMfpCsv: async (file: File): Promise<ImportResult> => {
    const formData = new FormData();
    formData.append('file', file);
    // Note: httpClient wrapper helper usually handles JSON. 
    // We might need a raw fetch or verify if httpClient handles FormData.
    // Assuming httpClient needs adjustment or we use fetch directly for FormData if simple wrapper.
    // Let's assume we bypass or use a specific overload. 
    // If httpClient enforces Content-Type: application/json, this will fail.
    // Let's check httpClient implementation later. Ideally:
    
    // Using raw fetch for FormData to avoid Content-Type header issues with boundary
    const token = localStorage.getItem('auth_token'); // Or useStore
    const response = await fetch('/api/integrations/mfp/import', {
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
  },

  // Zepp Life (CSV Import)
  uploadZeppLifeCsv: async (file: File): Promise<ImportResult> => {
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
  },

  // Telegram
  getTelegramStatus: async (): Promise<{ connected: boolean; username?: string } | undefined> => {
     return httpClient('/integrations/telegram/status');
  },
  
  generateTelegramCode: async (): Promise<{ code: string; url: string } | undefined> => {
     return httpClient('/integrations/telegram/code', { method: 'POST' });
  }
};
