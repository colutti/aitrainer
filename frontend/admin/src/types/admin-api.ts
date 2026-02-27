/**
 * Admin API Response Types
 * Synchronized with shared/types/admin.ts
 */

export interface AdminUser {
  email: string;
  name?: string;
  display_name?: string;
  is_admin: boolean;
  created_at?: string;
  last_login?: string;
  photo_base64?: string;
}

export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

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

export interface ApplicationLog {
  timestamp: string;
  level: string;
  message: string;
  module?: string;
}

export interface LogListResponse {
  logs: ApplicationLog[];
  total: number;
}

export interface ApplicationLogResponse {
  logs: string[];
  source: string;
  total: number;
}

export interface BetterStackLogResponse {
  data: Record<string, unknown>[];
  total: number;
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
  prompt?: {
    prompt?: string;
    type?: string;
    prompt_name?: string;
    messages?: { role: string; content: string }[];
    tools?: string[];
  };
  tokens_used?: number; // compat
  xml_content?: string; // compat
}

export interface PromptListResponse {
  prompts: PromptLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TokenSummary {
  _id: string;
  user_email?: string;
  total_input: number;
  total_output: number;
  message_count: number;
  last_activity: string;
  model: string;
  cost_usd?: number;
}

export interface TokenTimeseries {
  date: string;
  tokens_input: number;
  tokens_output: number;
}

export interface TokenSummaryResponse {
  data: TokenSummary[];
  total_users_with_tokens: number;
}

export interface TokenTimeseriesResponse {
  data: TokenTimeseries[];
  data_points: number;
}

export interface LoginResponse {
  token: string;
}

export interface UserMeResponse {
  email: string;
  name?: string;
  role: 'admin' | 'user';
  photo_base64?: string;
}
