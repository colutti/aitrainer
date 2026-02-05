import { describe, expect, it, vi, beforeEach } from 'vitest';

import { httpClient } from '../../../shared/api/http-client';
import { integrationsApi } from './integrations-api';

vi.mock('../../../shared/api/http-client', () => ({
  httpClient: vi.fn(),
}));

// Mock global fetch for file uploads
global.fetch = vi.fn();

describe('integrationsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => 'mock-token'),
    });
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
      body: JSON.stringify({ api_key: 'key-123' })
    });
  });

  it('should upload MFP CSV', async () => {
    const file = new File(['content'], 'test.csv', { type: 'text/csv' });
    const mockRes = { imported: 10 };
    
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => mockRes
    } as Response);

    const res = await integrationsApi.uploadMfpCsv(file);
    
    expect(res).toEqual(mockRes);
    expect(global.fetch).toHaveBeenCalledWith('/api/integrations/mfp/import', expect.objectContaining({
      method: 'POST',
      headers: { Authorization: 'Bearer mock-token' },
      body: expect.any(FormData)
    }));
  });

  it('should get Telegram status', async () => {
    await integrationsApi.getTelegramStatus();
    expect(httpClient).toHaveBeenCalledWith('/integrations/telegram/status');
  });
});
