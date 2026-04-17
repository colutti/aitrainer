import { beforeEach, describe, expect, it } from 'vitest';

import { getRuntimeConfig, getRuntimeConfigValue } from './runtime-config';

describe('runtime config', () => {
  beforeEach(() => {
    delete window.__APP_CONFIG__;
  });

  it('returns empty config when runtime config is absent', () => {
    expect(getRuntimeConfig()).toEqual({});
  });

  it('reads runtime config values from window', () => {
    window.__APP_CONFIG__ = {
      VITE_FIREBASE_API_KEY: 'runtime-key',
      VITE_API_URL: '/runtime-api',
    };

    expect(getRuntimeConfig()).toEqual({
      VITE_FIREBASE_API_KEY: 'runtime-key',
      VITE_API_URL: '/runtime-api',
    });
    expect(getRuntimeConfigValue('VITE_FIREBASE_API_KEY')).toBe('runtime-key');
    expect(getRuntimeConfigValue('VITE_API_URL')).toBe('/runtime-api');
  });
});
