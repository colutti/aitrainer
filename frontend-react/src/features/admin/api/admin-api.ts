import { httpClient } from '../../../shared/api/http-client';

export interface AdminOverview {
  total_users: number;
  total_admins: number;
  active_users_7d: number;
  active_users_24h: number;
  total_messages: number;
  total_workouts: number;
  total_nutrition_logs: number;
}

export interface QualityMetrics {
  avg_messages_per_user: number;
  workout_engagement_rate: number;
  nutrition_engagement_rate: number;
}

export interface AdminUser {
  email: string;
  name?: string;
  is_admin: boolean;
  created_at?: string;
  last_login?: string;
  // Add other fields as needed
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  module?: string;
  // Add fields
}

export interface PromptLog {
  id: string;
  user_email: string;
  timestamp: string;
  prompt_name?: string;
  model: string;
  tokens_input: number;
  tokens_output: number;
  duration_ms: number;
  status: 'success' | 'error';
}

export interface PromptListResponse {
  prompts: PromptLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const adminApi = {
  getOverview: async (): Promise<AdminOverview> => {
    return httpClient('/admin/analytics/overview');
  },

  getQualityMetrics: async (): Promise<QualityMetrics> => {
    return httpClient('/admin/analytics/quality-metrics');
  },

  listUsers: async (page = 1, pageSize = 20, search = ''): Promise<UserListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search) params.append('search', search);
    return httpClient(`/admin/users/list?${params.toString()}`);
  },

  getUserDetails: async (email: string): Promise<AdminUser> => {
    return httpClient(`/admin/users/${encodeURIComponent(email)}/details`);
  },

  updateUser: async (email: string, updates: Partial<AdminUser>): Promise<AdminUser> => {
    return httpClient(`/admin/users/${encodeURIComponent(email)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  deleteUser: async (email: string): Promise<{ success: boolean }> => {
    return httpClient(`/admin/users/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });
  },

  getApplicationLogs: async (limit = 100, level?: string): Promise<{ logs: string[]; source: string; total: number }> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (level) params.append('level', level);
    return httpClient(`/admin/logs/application?${params.toString()}`);
  },

  getBetterStackLogs: async (limit = 100, query?: string): Promise<any> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (query) params.append('query', query);
    return httpClient(`/admin/logs/betterstack?${params.toString()}`);
  },

  listPrompts: async (page = 1, pageSize = 20, userEmail = ''): Promise<PromptListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (userEmail) params.append('user_email', userEmail);
    return httpClient(`/admin/prompts/list?${params.toString()}`);
  },
};
