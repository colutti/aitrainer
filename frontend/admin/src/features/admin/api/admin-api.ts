import { httpClient } from '../../../shared/api/http-client';
import type {
  AdminOverview,
  AdminUser,
  PromptListResponse,
  PromptLog,
  QualityMetrics,
  TokenSummaryResponse,
  TokenTimeseriesResponse,
  UserListResponse,
} from '../../../types/admin-api';

export const adminApi = {
  getOverview: async (): Promise<AdminOverview> => {
    return httpClient<AdminOverview>('/admin/analytics/overview');
  },

  getQualityMetrics: async (): Promise<QualityMetrics> => {
    return httpClient<QualityMetrics>('/admin/analytics/quality-metrics');
  },

  listUsers: async (page = 1, pageSize = 20, search = ''): Promise<UserListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) params.append('search', search);
    return httpClient<UserListResponse>(`/admin/users/?${params.toString()}`);
  },

  getUser: async (email: string): Promise<AdminUser> => {
    return httpClient<AdminUser>(`/admin/users/${email}`);
  },

  updateUser: async (email: string, data: Partial<AdminUser>): Promise<AdminUser> => {
    return httpClient<AdminUser>(`/admin/users/${email}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  deleteUser: async (email: string): Promise<{ success: boolean }> => {
    return httpClient<{ success: boolean }>(`/admin/users/${email}`, {
      method: 'DELETE',
    });
  },


  listPrompts: async (page = 1, pageSize = 20, userId?: string): Promise<PromptListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (userId) params.append('user_id', userId);
    return httpClient<PromptListResponse>(`/admin/prompts/?${params.toString()}`);
  },

  getPrompt: async (id: string): Promise<PromptLog> => {
    return httpClient<PromptLog>(`/admin/prompts/${id}`);
  },

  getTokenSummary: async (days = 30): Promise<TokenSummaryResponse> => {
    const params = new URLSearchParams({ days: days.toString() });
    return httpClient<TokenSummaryResponse>(`/admin/tokens/summary?${params.toString()}`);
  },

  getTokenTimeseries: async (days = 30, userEmail?: string): Promise<TokenTimeseriesResponse> => {
    const params = new URLSearchParams({ days: days.toString() });
    if (userEmail) params.append('user_email', userEmail);
    return httpClient<TokenTimeseriesResponse>(`/admin/tokens/timeseries?${params.toString()}`);
  },
};
