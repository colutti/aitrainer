import { test as base, expect, type Page } from '@playwright/test';

import { VirtualBackend } from './helpers/virtual-backend';

/**
 * Interface for our custom fixtures
 */
interface MyFixtures {
  virtualBackend: VirtualBackend;
  authenticatedPage: Page;
  api: VirtualBackend; // Alias for tests using cleanupUserData(api)
}

export const test = base.extend<MyFixtures>({
  // Initialize the virtual backend state for each test
  virtualBackend: async (_, use) => {
    const vb = new VirtualBackend();
    await use(vb);
  },

  // Alias 'api' to 'virtualBackend'
  api: async ({ virtualBackend }, use) => {
    await use(virtualBackend);
  },

  // Authenticated page fixture with global mocking
  authenticatedPage: async ({ page, virtualBackend }, use) => {
    const email = 'e2e-bot@fityq.it';
    const token = 'mock-v-token';

    // 1. Mock Firebase Globals (satisfy SDK)
    const firebaseMockResponse = {
        kind: 'identitytoolkit#VerifyPasswordResponse',
        localId: 'mock-id',
        email: email,
        displayName: 'E2E Bot',
        idToken: 'mock-id-token',
        registered: true,
        refreshToken: 'mock-refresh-token',
        expiresIn: '3600',
        users: [{ localId: 'mock-id', email: email, emailVerified: true }]
    };

    await page.route('https://identitytoolkit.googleapis.com/**', async (route) => {
        await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(firebaseMockResponse) });
    });

    await page.route('https://securetoken.googleapis.com/**', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ access_token: 'mock-token', expires_in: '3600', id_token: 'mock-id-token', user_id: 'mock-id' })
        });
    });

    // 2. Intercept Backend API calls
    await page.route(url => url.pathname.includes('/api/'), async (route) => {
        const method = route.request().method();
        const url = route.request().url();
        let postData;
        try {
            postData = route.request().postDataJSON();
        } catch (e) {
            postData = undefined;
        }
        
        const response = await virtualBackend.handleRequest(method, url, postData);
        
        await route.fulfill({
            status: response.status,
            contentType: response.contentType || 'application/json',
            body: typeof response.body === 'string' ? response.body : JSON.stringify(response.body)
        });
    });

    // 3. Inject Auth Token and verify it's there
    await page.addInitScript(({ t }: { t: string }) => {
        window.localStorage.setItem('auth_token', t);
        window.localStorage.setItem('i18nextLng', 'pt-BR');
        // Clear onboarding tour
        window.localStorage.setItem('has_seen_tour_dashboard-main-e2e-bot@fityq.it', 'true');
    }, { t: token });

    // 4. Navigate and VERIFY AUTHENTICATION
    await page.goto('/dashboard');
    
    // If we are still on login page, something is wrong
    await expect(page).not.toHaveURL(/.*login/, { timeout: 10000 });
    
    // Check for root
    await expect(page.locator('#root')).toBeVisible({ timeout: 15000 });
    
    await use(page);
  }
});

export { expect };
