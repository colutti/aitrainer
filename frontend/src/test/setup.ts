import '@testing-library/jest-dom/vitest';
import { beforeEach, vi } from 'vitest';

/**
 * Global test setup for Vitest
 * Configures testing-library matchers and any global test utilities
 */

// Mock ResizeObserver for Recharts
global.ResizeObserver = class ResizeObserver {
  observe() { /* mock */ }
  unobserve() { /* mock */ }
  disconnect() { /* mock */ }
};

// Mock localStorage for all tests
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
});

// Clear localStorage before each test
beforeEach(() => {
  localStorageMock.clear();
});

// Mock fetch globally
global.fetch = vi.fn();
