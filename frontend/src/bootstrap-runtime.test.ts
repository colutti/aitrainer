import { describe, expect, it, vi } from 'vitest';

import { loadRuntimeConfig } from './bootstrap-runtime';

describe('loadRuntimeConfig', () => {
  it('initializes window.__APP_CONFIG__ and appends the runtime config script', async () => {
    const appendChild = vi.spyOn(document.head, 'appendChild');
    delete window.__APP_CONFIG__;

    const loadPromise = loadRuntimeConfig(window, document, 1000);
    const script = appendChild.mock.calls[0]?.[0] as HTMLScriptElement | undefined;

    expect(window.__APP_CONFIG__).toEqual({});
    expect(script).toBeDefined();
    expect(script?.src).toContain('/runtime-config.js');

    script?.dispatchEvent(new Event('load'));
    await loadPromise;
  });

  it('resolves when the runtime config script fails', async () => {
    const appendChild = vi.spyOn(document.head, 'appendChild');

    const loadPromise = loadRuntimeConfig(window, document, 1000);
    const script = appendChild.mock.calls[0]?.[0] as HTMLScriptElement | undefined;

    script?.dispatchEvent(new Event('error'));
    await expect(loadPromise).resolves.toBeUndefined();
  });

  it('resolves after the timeout when the runtime config script stalls', async () => {
    vi.useFakeTimers();

    const loadPromise = loadRuntimeConfig(window, document, 25);
    await vi.advanceTimersByTimeAsync(25);

    await expect(loadPromise).resolves.toBeUndefined();

    vi.useRealTimers();
  });
});
