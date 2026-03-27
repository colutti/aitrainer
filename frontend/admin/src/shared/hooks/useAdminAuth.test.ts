import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';

import { useAdminAuthStore } from './useAdminAuth';

vi.mock('../api/http-client', () => ({ httpClient: vi.fn() }));

describe('useAdminAuthStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useAdminAuthStore.setState({
      isAuthenticated: false,
      userInfo: null,
      isLoading: true,
      loginError: null,
    });
  });

  it('stores the token and loads admin user info on login', async () => {
    vi.mocked(httpClient)
      .mockResolvedValueOnce({ token: 'admin-token' } as never)
      .mockResolvedValueOnce({
        email: 'admin@fityq.com',
        role: 'admin',
        name: 'Admin',
      } as never);

    await useAdminAuthStore.getState().login('admin@fityq.com', 'secret');

    expect(localStorage.getItem('admin_auth_token')).toBe('admin-token');
    expect(useAdminAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAdminAuthStore.getState().userInfo).toEqual({
      email: 'admin@fityq.com',
      name: 'Admin',
    });
  });

  it('stops init when token is missing', async () => {
    await useAdminAuthStore.getState().init();

    expect(useAdminAuthStore.getState().isLoading).toBe(false);
    expect(useAdminAuthStore.getState().isAuthenticated).toBe(false);
  });
});
