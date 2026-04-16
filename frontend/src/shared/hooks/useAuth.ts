import { create } from 'zustand';

import { httpClient } from '../api/http-client';

import { usePublicConfigStore } from './usePublicConfig';

const AUTH_TOKEN_KEY = 'auth_token';
const DEMO_EMAIL = 'demo@fityq.it';
const DEMO_DISPLAY_NAME = 'Ethan Parker';
interface AuthBypassEnv {
  VITE_ENABLE_UNSAFE_LOCAL_AUTH_BYPASS?: string;
  PROD?: boolean;
  DEV?: boolean;
  MODE?: string;
}

export const shouldEnableUnsafeLocalAuthBypass = (env: AuthBypassEnv): boolean => {
  const flagEnabled = env.VITE_ENABLE_UNSAFE_LOCAL_AUTH_BYPASS === 'true';
  if (!flagEnabled) {
    return false;
  }

  // Hard stop: bypass is never allowed in production builds.
  if (env.PROD) {
    console.error('VITE_ENABLE_UNSAFE_LOCAL_AUTH_BYPASS is ignored in production.');
    return false;
  }

  if (env.DEV === true) {
    return true;
  }

  return env.MODE === 'test';
};

const UNSAFE_LOCAL_AUTH_BYPASS_ENABLED = shouldEnableUnsafeLocalAuthBypass(import.meta.env);

const createAuthError = (code: string, message: string): Error & { code: string } => {
  return Object.assign(new Error(message), { code });
};

export interface UserInfo {
  email: string;
  name: string;
  is_admin: boolean;
  is_demo?: boolean;
  photo_base64?: string;
  onboarding_completed: boolean;
  subscription_plan?: string;
  custom_message_limit?: number | null;
  custom_trial_days?: number | null;
  messages_sent_today?: number;
  trial_remaining_days?: number | null;
  current_daily_limit?: number | null;
  current_plan_limit?: number | null;
  effective_remaining_messages?: number | null;
  has_stripe_customer: boolean;
}

export interface AuthState {
  isAuthenticated: boolean;
  userInfo: UserInfo | null;
  isAdmin: boolean;
  isLoading: boolean;
}

export interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  socialLogin: (provider: 'google' | 'apple') => Promise<void>;
  requestPasswordReset: (email: string, locale?: string) => Promise<void>;
  logout: () => void;
  loadUserInfo: () => Promise<UserInfo>;
  getToken: () => string | null;
  init: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

export type AuthStore = AuthState & AuthActions;

const mapToFirebaseLanguageCode = (locale?: string): string => {
  const normalizedLocale = (locale ?? '').toLowerCase();
  if (normalizedLocale.startsWith('pt')) {
    return 'pt-BR';
  }
  if (normalizedLocale.startsWith('es')) {
    return 'es';
  }
  return 'en';
};

/**
 * Authentication store using Zustand
 */
export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  isAuthenticated: false,
  userInfo: null,
  isAdmin: false,
  isLoading: true,

  login: async (email: string, password: string) => {
    set({ isLoading: true });

    try {
      const normalizedEmail = email.trim().toLowerCase();
      if (UNSAFE_LOCAL_AUTH_BYPASS_ENABLED && normalizedEmail === DEMO_EMAIL) {
        const response = await httpClient<{ token: string }>('/user/e2e-login', {
          method: 'POST',
          body: JSON.stringify({
            email: DEMO_EMAIL,
            display_name: DEMO_DISPLAY_NAME,
          }),
        });

        if (!response?.token) {
          throw new Error('Invalid response from server');
        }

        localStorage.setItem(AUTH_TOKEN_KEY, response.token);
        await get().loadUserInfo();
        set({ isAuthenticated: true });
        return;
      }

      const { auth } = await import('../../features/auth/firebase');
      const { signInWithEmailAndPassword, sendEmailVerification, signOut } = await import('firebase/auth');
      
      const result = await signInWithEmailAndPassword(auth, email, password);

      if (!result.user.emailVerified) {
        await sendEmailVerification(result.user);
        await signOut(auth);
        throw createAuthError(
          'auth/email-not-verified',
          'Please verify your email before logging in',
        );
      }

      const token = await result.user.getIdToken();

      const response = await httpClient<{ token: string }>('/user/login', {
        method: 'POST',
        body: JSON.stringify({ token }),
      });

      if (!response?.token) {
        throw new Error('Invalid response from server');
      }

      localStorage.setItem(AUTH_TOKEN_KEY, response.token);
      await get().loadUserInfo();
      set({ isAuthenticated: true });
    } catch (error) {
      console.error('Login error:', error);
      get().logout();
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (name: string, email: string, password: string) => {
    set({ isLoading: true });

    try {
      const publicConfig = usePublicConfigStore.getState();
      if (!publicConfig.hasLoaded) {
        await publicConfig.load();
      }
      if (!usePublicConfigStore.getState().enableNewUserSignups) {
        throw createAuthError(
          'auth/new-signups-disabled',
          'New user signups are temporarily disabled',
        );
      }

      const normalizedEmail = email.trim().toLowerCase();
      if (UNSAFE_LOCAL_AUTH_BYPASS_ENABLED) {
        const response = await httpClient<{ token: string }>('/user/e2e-login', {
          method: 'POST',
          body: JSON.stringify({
            email: normalizedEmail,
            display_name: name.trim(),
            onboarding_completed: false,
            password,
          }),
        });

        if (!response?.token) {
          throw new Error('Invalid response from server');
        }

        localStorage.setItem(AUTH_TOKEN_KEY, response.token);
        await get().loadUserInfo();
        set({ isAuthenticated: true });
        return;
      }

      const { auth } = await import('../../features/auth/firebase');
      const { createUserWithEmailAndPassword, sendEmailVerification, signOut } = await import('firebase/auth');

      const result = await createUserWithEmailAndPassword(auth, normalizedEmail, password);
      await sendEmailVerification(result.user);
      await signOut(auth);
      localStorage.removeItem(AUTH_TOKEN_KEY);
      set({ isAuthenticated: false, userInfo: null, isAdmin: false });
    } catch (error) {
      console.error('Registration error:', error);
      get().logout();
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  socialLogin: async (providerName: 'google' | 'apple') => {
    set({ isLoading: true });

    try {
      const { auth } = await import('../../features/auth/firebase');
      const { signInWithPopup, GoogleAuthProvider, OAuthProvider } = await import('firebase/auth');
      
      const provider = providerName === 'google' 
        ? new GoogleAuthProvider() 
        : new OAuthProvider('apple.com');
        
      const result = await signInWithPopup(auth, provider);
      const token = await result.user.getIdToken();
      
      const response = await httpClient<{ token: string }>('/user/login', {
        method: 'POST',
        body: JSON.stringify({ token }),
      });

      if (!response?.token) {
        throw new Error('Invalid response from server');
      }

      localStorage.setItem(AUTH_TOKEN_KEY, response.token);
      await get().loadUserInfo();
      set({ isAuthenticated: true });
    } catch (error) {
      console.error('Social login error:', error);
      get().logout();
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  requestPasswordReset: async (email: string, locale?: string) => {
    const normalizedEmail = email.trim().toLowerCase();
    const { auth } = await import('../../features/auth/firebase');
    const { sendPasswordResetEmail } = await import('firebase/auth');
    auth.languageCode = mapToFirebaseLanguageCode(locale);
    await sendPasswordResetEmail(auth, normalizedEmail, {
      handleCodeInApp: true,
      url: `${window.location.origin}/login`,
    });
  },

  logout: () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);

    // Also sign out from Firebase if we have it imported
    void import('../../features/auth/firebase')
      .then(({ auth }) => {
        void import('firebase/auth')
          .then(({ signOut }) => {
            void signOut(auth).catch((err: unknown) => {
              console.error('Firebase signOut error:', err);
            });
          })
          .catch(() => {
            // Ignore if firebase/auth cannot be loaded
          });
      })
      .catch(() => {
        // Ignore if firebase config cannot be loaded
      });

    set({
      isAuthenticated: false,
      userInfo: null,
      isAdmin: false,
    });
  },

  loadUserInfo: async () => {
    const data = await httpClient<{ 
      email: string; 
      role: string; 
      name?: string; 
      photo_base64?: string;
      onboarding_completed: boolean;
      subscription_plan: string;
      custom_message_limit: number | null;
      custom_trial_days: number | null;
      messages_sent_today: number;
      trial_remaining_days: number | null;
      current_daily_limit: number | null;
      current_plan_limit: number | null;
      effective_remaining_messages: number | null;
      has_stripe_customer: boolean;
      is_demo?: boolean;
    }>('/user/me');

    if (!data) {
      throw new Error('Failed to load user info');
    }

    const userInfo = {
      email: data.email,
      name: data.name ?? data.email.split('@')[0] ?? 'User',
      is_admin: data.role === 'admin',
      is_demo: data.is_demo ?? false,
      photo_base64: data.photo_base64,
      onboarding_completed: data.onboarding_completed,
      subscription_plan: data.subscription_plan,
      custom_message_limit: data.custom_message_limit,
      custom_trial_days: data.custom_trial_days,
      messages_sent_today: data.messages_sent_today,
      trial_remaining_days: data.trial_remaining_days,
      current_daily_limit: data.current_daily_limit,
      current_plan_limit: data.current_plan_limit,
      effective_remaining_messages: data.effective_remaining_messages,
      has_stripe_customer: data.has_stripe_customer,
    };

    set({
      userInfo,
      isAdmin: data.role === 'admin',
    });

    return userInfo;
  },

  getToken: () => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },

  init: async () => {
    const token = get().getToken();

    if (!token) {
      set({ isLoading: false });
      return;
    }

    set({ isLoading: true });

    try {
      await get().loadUserInfo();
      set({ isAuthenticated: true });
    } catch {
      get().logout();
    } finally {
      set({ isLoading: false });
    }
  },

  refreshToken: async (): Promise<boolean> => {
    const token = get().getToken();
    if (!token) {
      get().logout();
      return false;
    }

    try {
      const { API_BASE_URL } = await import('../api/http-client');
      const response = await fetch(`${API_BASE_URL}/user/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        get().logout();
        return false;
      }

      const data = (await response.json()) as { token?: string };
      if (!data.token) {
        get().logout();
        return false;
      }

      localStorage.setItem(AUTH_TOKEN_KEY, data.token);
      return true;
    } catch {
      get().logout();
      return false;
    }
  },
}));
