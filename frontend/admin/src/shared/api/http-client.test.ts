import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from './http-client';

vi.mock('../hooks/useAdminAuth', () => ({
  getAdminToken: () => 'admin-token',
}));

describe('admin httpClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('fetch', vi.fn());
  });

  it('adds auth header and parses json responses', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ ok: true }),
    } as Response);

    const result = await httpClient('/admin/users');

    expect(result).toEqual({ ok: true });
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8001/admin/users',
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );
    const headers = vi.mocked(fetch).mock.calls[0]?.[1]?.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer admin-token');
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('returns null on 204 responses', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      status: 204,
      headers: new Headers(),
    } as Response);

    const result = await httpClient('/admin/users', { method: 'DELETE' });
    expect(result).toBeNull();
  });
});
