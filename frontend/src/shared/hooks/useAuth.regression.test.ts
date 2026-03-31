import { act, renderHook } from '@testing-library/react';
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

// Mock localStorage
const mockStorage = new Map();
const mockLocalStorage = {
  getItem: vi.fn((key) => mockStorage.get(key) ?? null),
  setItem: vi.fn((key, value) => mockStorage.set(key, value)),
  removeItem: vi.fn((key) => mockStorage.delete(key)),
  clear: vi.fn(() => mockStorage.clear()),
};

describe('useAuth Regression Tests', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', mockLocalStorage);
    vi.clearAllMocks();
    mockStorage.clear();
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

  it('REPRO: should not be in (isAuthenticated=true AND isLoading=true) state during login', async () => {
    const mockLoginResponse = { token: 'test-token-123' };
    const mockUserApiData = {
      email: 'test@example.com',
      role: 'user',
      name: 'Test User',
      onboarding_completed: true,
      has_stripe_customer: false,
    };

    // Mock login response
    vi.mocked(httpClient).mockResolvedValueOnce(mockLoginResponse);
    
    // Mock user info response with a delay to catch the intermediate state
    let resolveUserInfo: (value: any) => void;
    const userInfoPromise = new Promise((resolve) => {
      resolveUserInfo = resolve;
    });
    vi.mocked(httpClient).mockReturnValueOnce(userInfoPromise);

    const { result } = renderHook(() => useAuthStore());

    // Start login
    let loginPromise: Promise<void>;
    await act(async () => {
      loginPromise = result.current.login('test@example.com', 'password123');
    });

    // WHAT IT SHOULD BE: isAuthenticated should NOT be true until loadUserInfo succeeds.
    // This avoids AuthGuard and ProtectedRoute returning null (black screen).
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true);
    expect(result.current.userInfo).toBeNull();

    // Finish loadUserInfo
    await act(async () => {
      resolveUserInfo!(mockUserApiData);
      await loginPromise!;
    });

    // Final state should be correct
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.userInfo).not.toBeNull();
  });

  it('REPRO: should handle loadUserInfo failure during login by resetting isAuthenticated', async () => {
    const mockLoginResponse = { token: 'test-token-123' };

    vi.mocked(httpClient).mockResolvedValueOnce(mockLoginResponse);
    vi.mocked(httpClient).mockRejectedValueOnce(new Error('Unauthorized'));

    const { result } = renderHook(() => useAuthStore());

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'password123');
      } catch (e) {
        // expected
      }
    });

    // If loadUserInfo fails, we should NOT be authenticated.
    // CURRENT BUG: isAuthenticated might be left at true if not handled.
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.userInfo).toBeNull();
  });
});
