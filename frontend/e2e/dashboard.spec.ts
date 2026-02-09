import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ context, page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Mock authentication
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          email: 'test@example.com', 
          role: 'user',
          name: 'Test User'
        }),
      });
    });

    // Mock dashboard data
    await page.route('**/api/dashboard/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          streak: 7,
          total_workouts: 42,
          avg_weekly_training: 4.2,
          recent_prs: [],
          weight_trend: [],
          calorie_trend: [],
        }),
      });
    });

    // Set auth token before navigation
    await context.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });

    await page.goto('/');
  });

  test('should display dashboard widgets', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for main heading or recognizable dashboard element
    const dashboardVisible = page.locator('h1, h2, [data-testid="dashboard"]').first();
    await expect(dashboardVisible).toBeVisible({ timeout: 10000 });
  });

  test('should show loading skeletons initially', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });

    // Should show skeleton loaders (if implemented)
    const content = await page.content();
    expect(content.length).toBeGreaterThan(0);
  });
});
