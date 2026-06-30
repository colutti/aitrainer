import type { Page } from '@playwright/test';
import { describe, expect, it, vi } from 'vitest';

import { buildE2EUserCredentials, gotoAppRoute, seedAuthToken } from '../../e2e/helpers/bootstrap';

describe('buildE2EUserCredentials', () => {
  it('keeps generated display names short and stable for onboarding', () => {
    const credentials = buildE2EUserCredentials(
      {
        titlePath: [
          'Dashboard Features',
          'should display all main dashboard widgets and data correctly',
        ],
        repeatEachIndex: 0,
      } as never,
    );

    expect(credentials.name).toMatch(/^E2E /);
    expect(credentials.name.length).toBeLessThanOrEqual(22);
    expect(credentials.email).toContain('@fityq.it');
  });
});

describe('gotoAppRoute', () => {
  it('uses commit plus a short settle wait for app navigation', async () => {
    const goto = vi.fn().mockResolvedValue(null);
    const waitForTimeout = vi.fn().mockResolvedValue(undefined);
    const page = {
      goto,
      waitForTimeout,
    } as unknown as Page;

    await gotoAppRoute(page, '/login');

    expect(goto).toHaveBeenCalledWith('/login', { waitUntil: 'commit' });
    expect(waitForTimeout).toHaveBeenCalledWith(250);
  });
});

describe('seedAuthToken', () => {
  it('primes localStorage before the first app navigation', async () => {
    const addInitScript = vi.fn().mockResolvedValue(undefined);
    const page = {
      addInitScript,
    } as unknown as Page;

    await seedAuthToken(page, 'token-123');

    expect(addInitScript).toHaveBeenCalledTimes(1);
    const [initializer, token] = addInitScript.mock.calls[0] ?? [];
    expect(typeof initializer).toBe('function');
    expect(token).toBe('token-123');
  });
});
