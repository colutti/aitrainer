/**
 * Admin API Response Types
 * Defines all types returned by the admin backend API
 */

// User types
export interface AdminUser {
  email: string;
  name: string;
  is_admin: boolean;
  photo_base64?: string;
}

export interface UserListResponse {
  data: AdminUser[];
  total: number;
  page: number;
  page_size: number;
}

// Dashboard types
export interface AdminOverview {
  total_users: number;
  active_users_7d: number;
  active_users_24h: number;
  total_messages: number;
  total_workouts: number;
}

export interface QualityMetrics {
  engagement_rate: number;
  avg_session_duration: number;
  user_retention: number;
}

// Log types
export interface ApplicationLog {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  source?: string;
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

export interface LogListResponse {
  logs: ApplicationLog[];
  total: number;
}

// Prompt types
export interface PromptLog {
  id: string;
  user_email: string;
  timestamp: string;
  model: string;
  tokens_used: number;
  xml_content: string;
}

export interface PromptListResponse {
  prompts: PromptLog[];
  total: number;
  page: number;
  page_size: number;
}

// Token types
export interface TokenSummary {
  user_email: string;
  total_tokens: number;
  avg_tokens_per_message: number;
}

export interface TokenTimeseries {
  timestamp: string;
  tokens: number;
}

export interface TokenSummaryResponse {
  data: TokenSummary[];
  total_users_with_tokens: number;
}

export interface TokenTimeseriesResponse {
  data: TokenTimeseries[];
  data_points: number;
}

// Auth types
export interface LoginResponse {
  token: string;
}

export interface UserMeResponse {
  email: string;
  name?: string;
  role: 'admin' | 'user';
  photo_base64?: string;
}
