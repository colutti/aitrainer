/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-assignment, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-return, @typescript-eslint/restrict-template-expressions, @typescript-eslint/no-empty-function, @typescript-eslint/no-unsafe-argument, @typescript-eslint/no-unsafe-call */
import '@testing-library/jest-dom/vitest';
import { beforeEach, vi } from 'vitest';

import ptBR from '../locales/pt-BR.json';

// Mock HTMLFormElement.prototype.requestSubmit for jsdom
// Always override to prevent JSDOM from logging "Not implemented" for requestSubmit.
// We use Object.defineProperty because JSDOM may define requestSubmit as non-writable,
// making direct assignment silently fail.
if (typeof HTMLFormElement !== 'undefined') {
  Object.defineProperty(HTMLFormElement.prototype, 'requestSubmit', {
    configurable: true,
    writable: true,
    value(submitter?: HTMLElement | null) {
      if (submitter) {
        submitter.click();
      } else {
        this.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      }
    },
  });
}

const tMock = (key: string, options?: any) => {
  const keys = key.split('.');
  let val: any = ptBR;
  for (const k of keys) {
    if (val && typeof val === 'object' && k in val) {
      val = val[k];
    } else {
      return key;
    }
  }
  
  if (typeof val === 'string') {
    // Basic interpolation mock for {{name}}, {{count}}, etc.
    if (options) {
      return val.replace(/\{\{([^}]+)\}\}/g, (_, varName) => {
        return options[varName] !== undefined ? String(options[varName]) : `{{${varName}}}`;
      });
    }
    return val;
  }
  
  if (Array.isArray(val) || (val && typeof val === 'object')) {
    return val;
  }

  return key;
};

const i18nMock = {
  changeLanguage: () => new Promise(() => {}),
  language: 'pt-BR',
  on: vi.fn(),
  off: vi.fn(),
};

const useTranslationMock = {
  t: tMock,
  i18n: i18nMock,
};

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => useTranslationMock,
    initReactI18next: {
      type: '3rdParty',
      init: vi.fn(),
    },
    Trans: ({ children, i18nKey }: any) => {
       const keys = typeof i18nKey === 'string' ? i18nKey.split('.') : [];
       let val: any = ptBR;
       for (const k of keys) {
         if (val && typeof val === 'object' && k in val) val = val[k];
         else return children;
       }
       return typeof val === 'string' ? val : children;
    },
  };
});


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

// Mock Recharts ResponsiveContainer to suppress "width(0) and height(0)" warnings
vi.mock('recharts', async (importOriginal) => {
  const React = await import('react');
  const original = await importOriginal<typeof import('recharts')>();
  return {
    ...original,
    ResponsiveContainer: ({ children, width = 800, height = 400 }: any) =>
      React.createElement(
        'div',
        { style: { width, height } },
        typeof children === 'function'
          ? children({
              width: typeof width === 'number' ? width : 800,
              height: typeof height === 'number' ? height : 400,
            })
          : children
      ),
  };
});

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
