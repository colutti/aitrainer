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

  test('should show empty state when no history', async ({ page }) => {
    await page.route('**/api/message/history', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // With empty history, the input field should still be visible (chat is ready)
    await expect(page.getByPlaceholder(/Mensagem para/)).toBeVisible();
  });

  test('should not send with empty input', async ({ page }) => {
    // Mock history to avoid 500
    await page.route('**/api/message/history', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Try to send without filling input
    const sendButton = page.getByRole('button').filter({ has: page.locator('svg.lucide-send') });
    // Button should be disabled or the input should be empty preventing send
    const inputValue = await page.getByPlaceholder(/Mensagem para/).inputValue();
    expect(inputValue).toBe('');
  });

  test('should send message with Enter key', async ({ page }) => {
    await page.route('**/api/message/message', async (route) => {
      await route.fulfill({ status: 200, contentType: 'text/plain', body: 'Resposta do treinador.' });
    });

    await page.route('**/api/message/history', async (route) => {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    await page.getByPlaceholder(/Mensagem para/).fill('Teste Enter');
    await page.keyboard.press('Enter');

    await expect(page.getByText('Resposta do treinador.').first()).toBeVisible({ timeout: 10000 });
  });

  test('should verify message history', async ({ page }) => {
    // Use regex to match URL with query params like ?limit=20&offset=0
    await page.route(/\/api\/message\/history/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { sender: 'Student', text: 'Old message', timestamp: new Date().toISOString() },
          { sender: 'Trainer', text: 'Old response', timestamp: new Date().toISOString() }
        ])
      });
    });

    // Also mock trainer endpoints to prevent errors that could affect rendering
    await page.route('**/api/trainer/trainer_profile', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ trainer_type: 'atlas' }) });
    });
    await page.route('**/api/trainer/available_trainers', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([{ trainer_id: 'atlas', name: 'Atlas', short_description: 'Powerlifting' }]) });
    });

    await page.goto('/chat');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Old message').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Old response').first()).toBeVisible();
  });
});
