import { test, expect } from '@playwright/test';

test.describe('Chat Feature', () => {
  test.beforeEach(async ({ context, page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Mock user profile
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ name: 'User', email: 'user@ex.com' }) });
    });

    // Set auth token before navigation
    await context.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
    });
    
    await page.goto('/chat');
  });

  test('should send a message and receive response', async ({ page }) => {
    
    // Mock the streaming chat API
    // Playwright doesn't easily mock EventSource/SSE but we can mock the fetch that might initiate it
    // or just check the UI flow.
    
    await page.route('**/api/message/message', async (route) => {
      // Stream simulation
      await route.fulfill({
        status: 200,
        contentType: 'text/plain',
        body: 'Sua meta é 180g.'
      });
    });

    await page.getByPlaceholder(/Mensagem para/).fill('Qual minha meta de proteína?');
    await page.getByRole('button').filter({ has: page.locator('svg.lucide-send') }).click();

    // Wait for AI response (this might need adjustments depending on how streaming is implemented in UI)
    await expect(page.getByText('Sua meta é 180g.')).toBeVisible({ timeout: 10000 });
  });

  test('should verify message history', async ({ page }) => {
    await page.route('**/api/message/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { sender: 'Student', text: 'Old message', timestamp: new Date().toISOString() },
          { sender: 'Trainer', text: 'Old response', timestamp: new Date().toISOString() }
        ])
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Old message').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Old response').first()).toBeVisible();
  });
});
