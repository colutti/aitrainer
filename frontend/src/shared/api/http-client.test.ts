import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';

import { httpClient } from './http-client';

describe('httpClient', () => {
  const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
    vi.stubGlobal('localStorage', mockLocalStorage);
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('should make a successful GET request without token', async () => {
    const mockData = { id: 1, name: 'Test' };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(mockData),
    } as Response);

    const result = await httpClient('/test');
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
      headers: { 'Content-Type': 'application/json' }
    }));
  });

  it('should include Authorization header when token exists', async () => {
    mockLocalStorage.getItem.mockReturnValue('test-token');
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    } as Response);

    await httpClient('/test');
    expect(fetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token',
      }
    }));
  });

  it('should handle 401 Unauthorized and clear token', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Expired' }),
    } as Response);

    await expect(httpClient('/test')).rejects.toThrow('Expired');
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
  });

  it('should handle 401 with JSON parse error', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.reject(new Error('Parse Error')),
    } as Response);

    await expect(httpClient('/test')).rejects.toThrow('Unauthorized');
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
  });

  it('should handle generic HTTP error', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Server Error' }),
    } as Response);

    await expect(httpClient('/test')).rejects.toThrow('Server Error');
  });

  it('should handle generic HTTP error with JSON parse error', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error('Parse Error')),
    } as Response);

    await expect(httpClient('/test')).rejects.toThrow('HTTP error 500');
  });

  it('should return undefined for 204 No Content', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 204,
      json: () => Promise.resolve({}), // Should not be called
    } as Response);

    const result = await httpClient('/test');
    expect(result).toBeUndefined();
  });

  it('should return undefined when JSON parsing fails (e.g. empty body)', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.reject(new Error('Empty body')),
    } as Response);

    const result = await httpClient('/test');
    expect(result).toBeUndefined();
  });

  it('should propagate Error instances', async () => {
    const error = new Error('Fetch failed');
    vi.mocked(fetch).mockRejectedValue(error);

    await expect(httpClient('/test')).rejects.toThrow('Fetch failed');
  });

  it('should handle non-Error rejections as Network error', async () => {
    vi.mocked(fetch).mockRejectedValue('String error');

    await expect(httpClient('/test')).rejects.toThrow('Network error');
  });
});
