import { create } from 'zustand';

import { httpClient } from '../api/http-client';

const AUTH_TOKEN_KEY = 'auth_token';

export interface UserInfo {
  email: string;
  name: string;
  is_admin: boolean;
  photo_base64?: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  userInfo: UserInfo | null;
  isAdmin: boolean;
  isLoading: boolean;
}

export interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loadUserInfo: () => Promise<void>;
  getToken: () => string | null;
  init: () => Promise<void>;
}

export type AuthStore = AuthState & AuthActions;

/**
 * Authentication store using Zustand
 *
 * Manages user authentication state, login/logout, and user information.
 * Token is stored in localStorage and automatically attached to API requests.
 *
 * @example
 * ```tsx
 * function LoginPage() {
 *   const { login, isAuthenticated } = useAuthStore();
 *
 *   const handleLogin = async () => {
 *     await login('user@example.com', 'password');
 *   };
 *
 *   return <button onClick={handleLogin}>Login</button>;
 * }
 * ```
 */
export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  isAuthenticated: false,
  userInfo: null,
  isAdmin: false,
  isLoading: false,

  /**
   * Login with email and password
   * Stores the JWT token in localStorage and loads user info
   */
  login: async (email: string, password: string) => {
    set({ isLoading: true });

    try {
      const response = await httpClient<{ token: string }>('/user/login', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!response?.token) {
        throw new Error('Invalid response from server');
      }

      localStorage.setItem(AUTH_TOKEN_KEY, response.token);
      set({ isAuthenticated: true });

      await get().loadUserInfo();
    } finally {
      set({ isLoading: false });
    }
  },

  /**
   * Logout and clear all auth state
   * Removes token from localStorage and resets state
   */
  logout: () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    set({
      isAuthenticated: false,
      userInfo: null,
      isAdmin: false,
    });
  },

  /**
   * Load current user information from API
   * Sets userInfo and isAdmin based on response
   */
  loadUserInfo: async () => {
    const data = await httpClient<{ email: string; role: string; name?: string; photo_base64?: string }>('/user/me');

    if (!data) {
      throw new Error('Failed to load user info');
    }

    set({
      userInfo: {
        email: data.email,
        name: data.name ?? data.email.split('@')[0] ?? 'User',
        is_admin: data.role === 'admin',
        photo_base64: data.photo_base64,
      },
      isAdmin: data.role === 'admin',
    });
  },

  /**
   * Get the current auth token from localStorage
   */
  getToken: () => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },

  /**
   * Initialize auth state on app startup
   * Checks for existing token and loads user info if present
   */
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
      // Token is invalid, logout
      get().logout();
    } finally {
      set({ isLoading: false });
    }
  },
}));
