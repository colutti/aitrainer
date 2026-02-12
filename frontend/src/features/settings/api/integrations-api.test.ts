import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';

import { integrationsApi } from './integrations-api';

// Mock httpClient
vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

describe('integrationsApi', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'mock-token'),
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
    vi.unstubAllGlobals();
  });

  it('should get Hevy status', async () => {
    const mockRes = { enabled: true, hasKey: true };
    vi.mocked(httpClient).mockResolvedValue(mockRes);
    const res = await integrationsApi.getHevyStatus();
    expect(res).toEqual(mockRes);
    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/status');
  });

  it('should save Hevy key', async () => {
    await integrationsApi.saveHevyKey('key-123');
    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/config', {
      method: 'POST',
      body: JSON.stringify({ api_key: 'key-123', enabled: true })
    });
  });

  it('should remove Hevy key', async () => {
    await integrationsApi.removeHevyKey();
    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/config', {
      method: 'POST',
      body: JSON.stringify({ api_key: '', enabled: false })
    });
  });

  it('should sync Hevy', async () => {
    const mockRes = { imported: 5, skipped: 0 };
    vi.mocked(httpClient).mockResolvedValue(mockRes);

    const res = await integrationsApi.syncHevy();

    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/import', {
      method: 'POST',
      body: JSON.stringify({ mode: 'skip_duplicates' })
    });
    expect(res).toEqual(mockRes);
  });

  it('should get webhook config', async () => {
    const mockRes = { hasWebhook: true, webhookUrl: 'https://example.com/webhook', authHeader: 'Bearer ****' };
    vi.mocked(httpClient).mockResolvedValue(mockRes);

    const res = await integrationsApi.getWebhookConfig();

    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/webhook/config');
    expect(res).toEqual(mockRes);
  });

  it('should generate webhook', async () => {
    const mockRes = { webhookUrl: 'https://example.com/webhook/new', authHeader: 'Bearer secret' };
    vi.mocked(httpClient).mockResolvedValue(mockRes);

    const res = await integrationsApi.generateWebhook();

    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/webhook/generate', { method: 'POST' });
    expect(res).toEqual(mockRes);
  });

  it('should revoke webhook', async () => {
    await integrationsApi.revokeWebhook();
    expect(httpClient).toHaveBeenCalledWith('/integrations/hevy/webhook', { method: 'DELETE' });
  });

  it('should upload MFP CSV', async () => {
    const file = new File(['content'], 'test.csv', { type: 'text/csv' });
    const mockRes = { imported: 10 };
    
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRes)
    } as Response);

    const res = await integrationsApi.uploadMfpCsv(file);
    
    expect(res).toEqual(mockRes);
    expect(global.fetch).toHaveBeenCalledWith('/api/integrations/mfp/import', expect.objectContaining({
      method: 'POST',
      headers: { Authorization: 'Bearer mock-token' },
      body: expect.any(FormData)
    }));
  });

  it('should upload Zepp Life CSV', async () => {
    const file = new File(['content'], 'zepp.csv', { type: 'text/csv' });
    const mockRes = { imported: 5 };
    
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockRes)
    } as Response);

    const res = await integrationsApi.uploadZeppLifeCsv(file);
    
    expect(res).toEqual(mockRes);
    expect(global.fetch).toHaveBeenCalledWith('/api/integrations/zepp_life/import', expect.objectContaining({
      method: 'POST',
      headers: { Authorization: 'Bearer mock-token' },
      body: expect.any(FormData)
    }));
  });

  it('should get Telegram status', async () => {
    const mockRes = { linked: true, telegram_username: 'user' };
    vi.mocked(httpClient).mockResolvedValue(mockRes);

    const res = await integrationsApi.getTelegramStatus();

    expect(httpClient).toHaveBeenCalledWith('/telegram/status');
    expect(res).toEqual(mockRes);
  });

  it('should generate Telegram code', async () => {
    const mockRes = { code: '123456', url: 't.me/bot?start=123456' };
    vi.mocked(httpClient).mockResolvedValue(mockRes);

    const res = await integrationsApi.generateTelegramCode();

    expect(httpClient).toHaveBeenCalledWith('/telegram/generate-code', { method: 'POST' });
    expect(res).toEqual(mockRes);
  });

  it('should throw error on failed upload', async () => {
    const file = new File(['content'], 'test.csv', { type: 'text/csv' });
    
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      status: 500
    } as Response);

    await expect(integrationsApi.uploadMfpCsv(file)).rejects.toThrow('Falha no upload');
  });
});
