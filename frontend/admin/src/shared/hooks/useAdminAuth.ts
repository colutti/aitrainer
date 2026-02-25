import { create } from 'zustand';

import type { LoginResponse, UserMeResponse } from '../../types/admin-api';
import { httpClient } from '../api/http-client';

const ADMIN_TOKEN_KEY = 'admin_auth_token';

export interface AdminUserInfo {
  email: string;
  name: string;
}

export interface AdminAuthState {
  isAuthenticated: boolean;
  userInfo: AdminUserInfo | null;
  isLoading: boolean;
  loginError: string | null;
}

export interface AdminAuthActions {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUserInfo: () => Promise<void>;
  getToken: () => string | null;
  init: () => Promise<void>;
}

export type AdminAuthStore = AdminAuthState & AdminAuthActions;

/**
 * Admin authentication store
 * Isolated from main app auth with separate token key
 * Only allows users with is_admin: true
 */
export const useAdminAuthStore = create<AdminAuthStore>((set, get) => ({
  isAuthenticated: false,
  userInfo: null,
  isLoading: false,
  loginError: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, loginError: null });

    try {
      const response = await httpClient<LoginResponse>('/user/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (!response?.token) {
        throw new Error('Invalid response from server');
      }

      localStorage.setItem(ADMIN_TOKEN_KEY, response.token);
      set({ isAuthenticated: true });

      await get().loadUserInfo();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      set({ loginError: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: () => {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    set({
      isAuthenticated: false,
      userInfo: null,
      loginError: null,
    });
  },

  loadUserInfo: async () => {
    const data = await httpClient<UserMeResponse>('/user/me');

    if (!data) {
      throw new Error('Failed to load user info');
    }

    // Only admin users can access the admin app
    if (data.role !== 'admin') {
      get().logout();
      throw new Error('Access denied: admin role required');
    }

    set({
      userInfo: {
        email: data.email,
        name: data.name ?? data.email.split('@')[0] ?? 'Admin',
      },
    });
  },

  getToken: () => {
    return localStorage.getItem(ADMIN_TOKEN_KEY);
  },

  init: async () => {
    const token = get().getToken();

    if (!token) {
      return;
    }

    set({ isLoading: true });

    try {
      set({ isAuthenticated: true });
      await get().loadUserInfo();
    } catch {
      get().logout();
    } finally {
      set({ isLoading: false });
    }
  },
}));

// Helper for httpClient to access token
export function getAdminToken(): string | null {
  return useAdminAuthStore.getState().getToken();
}
