import { httpClient } from '../../../shared/api/http-client';
import type {
  AdminOverview,
  AdminUser,
  PromptListResponse,
  PromptLog,
  QualityMetrics,
  UserListResponse,
} from '../../../shared/types/admin';

export const adminApi = {
  getOverview: async (): Promise<AdminOverview> => {
    return httpClient<AdminOverview>('/admin/analytics/overview') as Promise<AdminOverview>;
  },

  getQualityMetrics: async (): Promise<QualityMetrics> => {
    return httpClient<QualityMetrics>('/admin/analytics/quality-metrics') as Promise<QualityMetrics>;
  },

  listUsers: async (page = 1, pageSize = 20, search = ''): Promise<UserListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) params.append('search', search);
    return httpClient<UserListResponse>(`/admin/users/?${params.toString()}`) as Promise<UserListResponse>;
  },

  getUser: async (email: string): Promise<AdminUser> => {
    return httpClient<AdminUser>(`/admin/users/${email}`) as Promise<AdminUser>;
  },

  updateUser: async (email: string, data: Partial<AdminUser>): Promise<AdminUser> => {
    return httpClient<AdminUser>(`/admin/users/${email}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }) as Promise<AdminUser>;
  },

  deleteUser: async (email: string): Promise<{ success: boolean }> => {
    return httpClient<{ success: boolean }>(`/admin/users/${email}`, {
      method: 'DELETE',
    }) as Promise<{ success: boolean }>;
  },

  getApplicationLogs: async (limit = 100, level?: string): Promise<{ logs: string[]; source: string; total: number }> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (level) params.append('level', level);
    return httpClient<{ logs: string[]; source: string; total: number }>(`/admin/logs/application?${params.toString()}`) as Promise<{ logs: string[]; source: string; total: number }>;
  },

  getBetterStackLogs: async (limit = 100, query?: string): Promise<{ data: unknown[]; total: number }> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (query) params.append('query', query);
    return httpClient<{ data: unknown[]; total: number }>(`/admin/logs/betterstack?${params.toString()}`) as Promise<{ data: unknown[]; total: number }>;
  },

  listPrompts: async (page = 1, pageSize = 20, userId?: string): Promise<PromptListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (userId) params.append('user_id', userId);
    return httpClient<PromptListResponse>(`/admin/prompts/?${params.toString()}`) as Promise<PromptListResponse>;
  },

  getPrompt: async (id: string): Promise<PromptLog> => {
    return httpClient<PromptLog>(`/admin/prompts/${id}`) as Promise<PromptLog>;
  },
};
