/**
 * Admin API Response Types
 * Synchronized with shared/types/admin.ts
 */

export interface AdminUser {
  email: string;
  name?: string;
  display_name?: string;
  is_admin: boolean;
  is_demo?: boolean;
  created_at?: string;
  last_login?: string;
  photo_base64?: string;
  subscription_plan?: string;
  custom_message_limit?: number | null;
  custom_trial_days?: number | null;
  messages_sent_this_month?: number;
  total_messages_sent?: number;
  current_billing_cycle_start?: string;
}


export interface UserListResponse {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DemoSnapshot {
  snapshot_id: string;
  demo_email: string;
  source_user_email?: string;
  episode_count?: number;
  message_count?: number;
  created_at?: string;
}

export interface DemoEpisode {
  snapshot_id?: string;
  episode_id: string;
  title: string;
  started_at: string;
  ended_at: string;
  primary_domain: string;
  trainers: string[];
  published_message_ids?: string[];
  message_count?: number;
  score?: number;
  status?: string;
}

export interface DemoMessage {
  snapshot_id?: string;
  episode_id: string;
  message_id: string;
  role: string;
  trainer_type?: string;
  timestamp: string;
  content: string;
  status?: string;
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
    tools_called?: string[];
  };
  tokens_used?: number; // compat
  xml_content?: string; // compat
  prompt_format?: 'markdown' | 'xml_like' | 'plain_text' | 'unknown';
  raw_tools_called_count?: number;
  raw_tools_called?: string[];
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
