import { describe, expect, it } from 'vitest';

import { buildE2EUserCredentials } from '../../e2e/helpers/bootstrap';

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
