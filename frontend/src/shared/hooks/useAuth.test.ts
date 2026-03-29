import { act, renderHook, waitFor } from '@testing-library/react';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';

import { useAuthStore } from './useAuth';

// Mock the http-client module
vi.mock('../api/http-client');

// Mock Firebase
vi.mock('../../features/auth/firebase', () => ({
  auth: {
    currentUser: {
      getIdToken: vi.fn().mockResolvedValue('fake-id-token'),
    },
  },
}));

vi.mock('firebase/auth', () => ({
  signInWithEmailAndPassword: vi.fn().mockResolvedValue({
    user: {
      getIdToken: vi.fn().mockResolvedValue('fake-id-token'),
    },
  }),
  signInWithPopup: vi.fn().mockResolvedValue({
    user: {
      getIdToken: vi.fn().mockResolvedValue('fake-id-token'),
    },
  }),
  GoogleAuthProvider: vi.fn(),
  OAuthProvider: vi.fn(),
}));


// Mock localStorage with actual storage
const mockStorage = new Map();

const mockLocalStorage = {
  getItem: vi.fn((key) => mockStorage.get(key) ?? null),
  setItem: vi.fn((key, value) => mockStorage.set(key, value)),
  removeItem: vi.fn((key) => mockStorage.delete(key)),
  clear: vi.fn(() => mockStorage.clear()),
};

describe('useAuth', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', mockLocalStorage);
    vi.clearAllMocks();
    mockStorage.clear();
    mockLocalStorage.getItem.mockImplementation((key) => mockStorage.get(key) ?? null);
    mockLocalStorage.setItem.mockImplementation((key, value) => mockStorage.set(key, value));
    mockLocalStorage.removeItem.mockImplementation((key) => mockStorage.delete(key));
    // Reset Zustand store state
    useAuthStore.setState({
      isAuthenticated: false,
      userInfo: null,
      isAdmin: false,
      isLoading: false,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
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
    it('should bypass firebase for the local demo account', async () => {
      const mockLoginResponse = { token: 'demo-token-123' };
      const mockUserApiData = {
        email: 'demo@fityq.it',
        role: 'user',
        name: 'Ethan Parker',
        onboarding_completed: true,
        has_stripe_customer: false,
        is_demo: true,
      };

      vi.mocked(httpClient).mockResolvedValueOnce(mockLoginResponse);
      vi.mocked(httpClient).mockResolvedValueOnce(mockUserApiData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('demo@fityq.it', 'anything-here');
      });

      expect(signInWithEmailAndPassword).not.toHaveBeenCalled();
      expect(httpClient).toHaveBeenNthCalledWith(1, '/user/e2e-login', {
        method: 'POST',
        body: JSON.stringify({
          email: 'demo@fityq.it',
          display_name: 'Ethan Parker',
        }),
      });
      expect(httpClient).toHaveBeenNthCalledWith(2, '/user/me');
      expect(localStorage.getItem('auth_token')).toBe('demo-token-123');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.userInfo).toEqual(expect.objectContaining({
        email: 'demo@fityq.it',
        name: 'Ethan Parker',
        is_demo: true,
      }));
    });

    it('should login with valid credentials and set token', async () => {
      const mockLoginResponse = { token: 'test-token-123' };
      const mockUserApiData = {
        email: 'test@example.com',
        role: 'user',
        name: 'Test User',
        onboarding_completed: true,
        has_stripe_customer: false,
      };
      
      const expectedUserInfo = {
         email: 'test@example.com',
         name: 'Test User',
         is_admin: false,
         photo_base64: undefined,
         onboarding_completed: true,
         has_stripe_customer: false,
      };

      // Mock login response
      vi.mocked(httpClient).mockResolvedValueOnce(mockLoginResponse);
      // Mock user info response
      vi.mocked(httpClient).mockResolvedValueOnce(mockUserApiData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.login('test@example.com', 'password123');
      });

      expect(signInWithEmailAndPassword).toHaveBeenCalled();
      expect(httpClient).toHaveBeenNthCalledWith(1, '/user/login', {
        method: 'POST',
        body: JSON.stringify({
          token: 'fake-id-token',
        }),
      });

      expect(httpClient).toHaveBeenNthCalledWith(2, '/user/me');

      expect(localStorage.getItem('auth_token')).toBe('test-token-123');
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.userInfo).toEqual(expect.objectContaining(expectedUserInfo));
    });

    it('should throw error with invalid credentials', async () => {
      vi.mocked(signInWithEmailAndPassword).mockRejectedValueOnce(new Error('Invalid credentials'));

      const { result } = renderHook(() => useAuthStore());

      await expect(
        act(async () => {
          await result.current.login('test@example.com', 'wrong-password');
        })
      ).rejects.toThrow('Invalid credentials');

      expect(result.current.isAuthenticated).toBe(false);
      expect(localStorage.getItem('auth_token')).toBeNull();
    });

    it('should throw error if login response is invalid (missing token)', async () => {
        vi.mocked(httpClient).mockResolvedValueOnce({}); // Empty object
  
        const { result } = renderHook(() => useAuthStore());
  
        await expect(
          act(async () => {
            await result.current.login('test@example.com', 'pass');
          })
        ).rejects.toThrow('Invalid response from server');
  
        expect(result.current.isAuthenticated).toBe(false);
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
          userInfo: { email: 'test@example.com', name: 'Test User', is_admin: true, onboarding_completed: true, has_stripe_customer: false },
          isAdmin: true,
          isLoading: false // Add isLoading mandatory field
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
      const mockUserApiData = {
        email: 'admin@example.com',
        role: 'admin',
        name: 'Admin User',
        onboarding_completed: true,
        has_stripe_customer: false,
      };
      
      const expectedUserInfo = {
        email: 'admin@example.com',
        name: 'Admin User',
        is_admin: true,
        onboarding_completed: true,
        has_stripe_customer: false,
      };

      vi.mocked(httpClient).mockResolvedValueOnce(mockUserApiData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUserInfo();
      });

      expect(httpClient).toHaveBeenCalledWith('/user/me');
      expect(result.current.userInfo).toEqual(expect.objectContaining(expectedUserInfo));
      expect(result.current.isAdmin).toBe(true);
    });

    it('should load user info and set isAdmin to false for regular user', async () => {
      const mockUserApiData = {
        email: 'user@example.com',
        role: 'user',
        name: 'Regular User',
        onboarding_completed: true,
        has_stripe_customer: false,
        is_demo: true,
      };
      
      const expectedUserInfo = {
        email: 'user@example.com',
        name: 'Regular User',
        is_admin: false,
        onboarding_completed: true,
        has_stripe_customer: false,
        is_demo: true,
      };

      vi.mocked(httpClient).mockResolvedValueOnce(mockUserApiData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.loadUserInfo();
      });

      expect(result.current.userInfo).toEqual(expect.objectContaining(expectedUserInfo));
      expect(result.current.isAdmin).toBe(false);
    });

    it('should default name map from email if name missing', async () => {
        const mockUserApiData = {
          email: 'user@example.com',
          role: 'user',
          onboarding_completed: true,
          has_stripe_customer: false,
        };
        
        const expectedUserInfo = {
          email: 'user@example.com',
          name: 'user', // extracted from email
          is_admin: false,
          onboarding_completed: true,
          has_stripe_customer: false,
        };
  
        vi.mocked(httpClient).mockResolvedValueOnce(mockUserApiData);
  
        const { result } = renderHook(() => useAuthStore());
  
        await act(async () => {
          await result.current.loadUserInfo();
        });
  
        expect(result.current.userInfo).toEqual(expect.objectContaining(expectedUserInfo));
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

    it('should throw error if user info is invalid (undefined)', async () => {
        vi.mocked(httpClient).mockResolvedValueOnce(undefined);
  
        const { result } = renderHook(() => useAuthStore());
  
        await expect(
          act(async () => {
            await result.current.loadUserInfo();
          })
        ).rejects.toThrow('Failed to load user info');
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

      const mockUserApiData = {
        email: 'user@example.com',
        role: 'user',
        name: 'Test User',
        onboarding_completed: true,
        has_stripe_customer: false,
      };
      
      const expectedUserInfo = {
        email: 'user@example.com',
        name: 'Test User',
        is_admin: false,
        onboarding_completed: true,
        has_stripe_customer: false,
      };

      vi.mocked(httpClient).mockResolvedValueOnce(mockUserApiData);

      const { result } = renderHook(() => useAuthStore());

      await act(async () => {
        await result.current.init();
      });

      await waitFor(() => {
        expect(result.current.isAuthenticated).toBe(true);
        expect(result.current.userInfo).toEqual(expect.objectContaining(expectedUserInfo));
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

  describe('refreshToken', () => {
    it('refreshToken method exists and is callable', () => {
      const store = useAuthStore.getState();
      expect(typeof store.refreshToken).toBe('function');
    });

    it('refreshToken returns false when no token exists', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);

      const result = await useAuthStore.getState().refreshToken();
      expect(result).toBe(false);
    });

    it('refreshToken stores new token on success', async () => {
      mockLocalStorage.getItem.mockReturnValue('old-token');

      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ token: 'new-token-xyz' }),
      }));

      const result = await useAuthStore.getState().refreshToken();
      expect(result).toBe(true);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'new-token-xyz');
    });

    it('refreshToken returns false on fetch failure', async () => {
      mockLocalStorage.getItem.mockReturnValue('expired-token');

      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: false,
      }));

      const result = await useAuthStore.getState().refreshToken();
      expect(result).toBe(false);
    });
  });
});
