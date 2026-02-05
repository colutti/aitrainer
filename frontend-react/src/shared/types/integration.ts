export interface IntegrationProvider {
  id: string;
  name: string;
  description: string;
  logoUrl?: string; // or icon class
  status: 'connected' | 'disconnected' | 'coming_soon' | 'paused';
  isEnabled: boolean;
}

export interface HevyConfig {
  apiKey: string;
  isEnabled: boolean;
}

export interface HevyStatus {
  enabled: boolean;
  hasKey: boolean;
  apiKeyMasked: string | null; // e.g. "****cdef"
  lastSync: string | null; // ISO date
}

export interface ImportResult {
  created: number;
  updated: number;
  errors: number;
  total_days: number;
  error_messages: string[];
}
