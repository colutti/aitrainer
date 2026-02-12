import type { ImportResult } from './import-result';

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

export interface HevyWebhookConfig {
  hasWebhook: boolean;
  webhookUrl: string | null;
  authHeader: string | null;
}

export interface HevyWebhookCredentials {
  webhookUrl: string;
  authHeader: string;
}

export type { ImportResult };
