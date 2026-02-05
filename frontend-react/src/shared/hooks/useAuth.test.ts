import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';

import { useAuthStore } from './useAuth';

// Mock the http-client module
vi.mock('../api/http-client');

describe('useAuth', () => {
  beforeEach(() => {
    // Reset the store state before each test
    useAuthStore.getState().logout();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.userInfo).toBeNull();
      expect(result.current.isAdmin).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('login', () => {
    it('should login with valid credentials and set token', async () => {
      const mockLoginResponse = { access_token: 'test-token-123' };
      const mockUserInfo = {
        email: 'test@example.com',
        name: 'Test User',
        is_admin: false,
      };

      // Mock login response
      vi.mocked(httpClient).mockResolvedValueOnce(mockLoginResponse);
      // Mock user info response
      vi.mocked(httpClient).mockResolvedValueOnce(mockUserInfo);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(httpClient).toHaveBeenNthCalledWith(1, '/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username: 'test@example.com',
          password: 'password123',
        }),
      });

      expect(httpClient).toHaveBeenNthCalledWith(2, '/users/me');

      expect(localStorage.getItem('auth_token')).toBe('test-token-123');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.userInfo).toEqual(mockUserInfo);
    });

    it('should throw error with invalid credentials', async () => {
      vi.mocked(httpClient).mockRejectedValueOnce(new Error('Invalid credentials'));

      const { result } = renderHook(() => useAuthStore());

      await expect(
        act(async () => {
          await result.current.login('test@example.com', 'wrong-password');
        })
      ).rejects.toThrow('Invalid credentials');

      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('auth_token')).toBeNull();
    });
  });

  describe('logout', () => {
    it('should clear token and reset state', () => {
      localStorage.setItem('auth_token', 'test-token');
      const { result } = renderHook(() => useAuthStore());

      // Set some state
      act(() => {
        useAuthStore.setState({
          isAuthenticated: true,
          userInfo: { email: 'test@example.com', name: 'Test User' },
          isAdmin: true,
        });
      });

      act(() => {
        result.current.logout();
      });

      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.userInfo).toBeNull();
      expect(result.current.isAdmin).toBe(false);
    });
  });

  describe('loadUserInfo', () => {
    it('should load user info and set isAdmin correctly for admin user', async () => {
      const mockUserInfo = {
        email: 'admin@example.com',
        name: 'Admin User',
        is_admin: true,
      };
      vi.mocked(httpClient).mockResolvedValueOnce(mockUserInfo);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUserInfo();
      });

      expect(httpClient).toHaveBeenCalledWith('/users/me');
      expect(result.current.userInfo).toEqual(mockUserInfo);
      expect(result.current.isAdmin).toBe(true);
    });

    it('should load user info and set isAdmin to false for regular user', async () => {
      const mockUserInfo = {
        email: 'user@example.com',
        name: 'Regular User',
        is_admin: false,
      };
      vi.mocked(httpClient).mockResolvedValueOnce(mockUserInfo);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUserInfo();
      });

      expect(result.current.userInfo).toEqual(mockUserInfo);
      expect(result.current.isAdmin).toBe(false);
    });

    it('should handle error when loading user info fails', async () => {
      vi.mocked(httpClient).mockRejectedValueOnce(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuthStore());

      await expect(
        act(async () => {
          await result.current.loadUserInfo();
        })
      ).rejects.toThrow('Unauthorized');

      expect(result.current.userInfo).toBeNull();
      expect(result.current.isAdmin).toBe(false);
    });
  });

  describe('getToken', () => {
    it('should return token from localStorage', () => {
      localStorage.setItem('auth_token', 'test-token-456');

      const { result } = renderHook(() => useAuthStore());

      expect(result.current.getToken()).toBe('test-token-456');
    });

    it('should return null when no token exists', () => {
      const { result } = renderHook(() => useAuthStore());

      expect(result.current.getToken()).toBeNull();
    });
  });

  describe('init', () => {
    it('should initialize auth state when token exists', async () => {
      localStorage.setItem('auth_token', 'existing-token');

      const mockUserInfo = {
        email: 'user@example.com',
        name: 'Test User',
        is_admin: false,
      };
      vi.mocked(httpClient).mockResolvedValueOnce(mockUserInfo);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.init();
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
        expect(result.current.userInfo).toEqual(mockUserInfo);
      });
    });

    it('should not initialize when no token exists', async () => {
      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.init();
      });

      expect(httpClient).not.toHaveBeenCalled();
      expect(result.current.isAuthenticated).toBe(false);
    });

    it('should logout if token is invalid during init', async () => {
      localStorage.setItem('auth_token', 'invalid-token');
      vi.mocked(httpClient).mockRejectedValueOnce(new Error('Unauthorized'));

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.init();
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(false);
        expect(localStorage.getItem('auth_token')).toBeNull();
      });
    });
  });
});
