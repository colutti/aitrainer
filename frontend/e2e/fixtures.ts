import { test as base, expect, type Page, type APIRequestContext, type TestInfo } from '@playwright/test';

import { bootstrapFreshUser, bootstrapRegisteredUser } from './helpers/bootstrap';
import { UIActions } from './helpers/ui-actions';

interface Fixtures {
  api: APIRequestContext;
  ui: UIActions;
  authenticatedPage: Page;
  freshUser: Page;
  seedMemory: (text: string) => Promise<void>;
}

const apiBaseURL = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000';

export const test = base.extend<Fixtures>({
  ui: async ({ page }, use) => {
    await use(new UIActions(page));
  },

  api: async ({ authenticatedPage, playwright }, use) => {
    const token = await authenticatedPage.evaluate(() => localStorage.getItem('auth_token') ?? '');
    const apiContext = await playwright.request.newContext({
      baseURL: apiBaseURL,
      extraHTTPHeaders: {
        Authorization: token ? `Bearer ${token}` : '',
        'Content-Type': 'application/json',
      },
    });

    await use(apiContext);
    await apiContext.dispose();
  },

  authenticatedPage: async ({ page }, use, testInfo: TestInfo) => {
    const bootstrappedPage = await bootstrapRegisteredUser(page, testInfo);
    await use(bootstrappedPage);
  },

  freshUser: async ({ page }, use, testInfo: TestInfo) => {
    const onboardingPage = await bootstrapFreshUser(page, testInfo);
    await use(onboardingPage);
  },

  seedMemory: async ({ api }, use) => {
    await use(async (text: string) => {
      await api.post('/memory', {
        data: { memory: text },
      });
    });
  },
});

export { expect };
