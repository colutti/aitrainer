import { beforeEach, describe, expect, it, vi } from 'vitest';

const initializeAppMock = vi.fn();
const getAuthMock = vi.fn();
const connectAuthEmulatorMock = vi.fn();

vi.mock('firebase/app', () => ({
  initializeApp: (...args: unknown[]) => initializeAppMock(...args),
}));

vi.mock('firebase/auth', () => ({
  getAuth: (...args: unknown[]) => getAuthMock(...args),
  connectAuthEmulator: (...args: unknown[]) => connectAuthEmulatorMock(...args),
}));

describe('firebase auth module', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    initializeAppMock.mockReturnValue({ name: 'test-app' });
    getAuthMock.mockReturnValue({ name: 'test-auth' });
  });

  it('does not initialize firebase on module import', async () => {
    await import('./firebase');

    expect(initializeAppMock).not.toHaveBeenCalled();
    expect(getAuthMock).not.toHaveBeenCalled();
  });

  it('initializes firebase auth on demand and reuses the same instance', async () => {
    const { getFirebaseAuth } = await import('./firebase');

    const firstAuth = getFirebaseAuth();
    const secondAuth = getFirebaseAuth();

    expect(initializeAppMock).toHaveBeenCalledTimes(1);
    expect(getAuthMock).toHaveBeenCalledTimes(1);
    expect(firstAuth).toBe(secondAuth);
  });

  it('falls back to runtime config when Vite build vars are missing', async () => {
    window.__APP_CONFIG__ = {
      VITE_FIREBASE_API_KEY: 'runtime-key',
      VITE_FIREBASE_AUTH_DOMAIN: 'runtime.firebaseapp.com',
      VITE_FIREBASE_PROJECT_ID: 'runtime-project',
      VITE_FIREBASE_STORAGE_BUCKET: 'runtime.firebasestorage.app',
      VITE_FIREBASE_MESSAGING_SENDER_ID: '123456',
      VITE_FIREBASE_APP_ID: '1:123456:web:runtime',
    };

    const { getFirebaseAuth } = await import('./firebase');

    getFirebaseAuth();

    expect(initializeAppMock).toHaveBeenCalledWith({
      apiKey: 'runtime-key',
      authDomain: 'runtime.firebaseapp.com',
      projectId: 'runtime-project',
      storageBucket: 'runtime.firebasestorage.app',
      messagingSenderId: '123456',
      appId: '1:123456:web:runtime',
    });
  });
});
