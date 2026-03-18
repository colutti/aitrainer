import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Default mock user profile
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          email: 'test@example.com', 
          role: 'user',
          name: 'Test User',
          onboarding_completed: true
        }),
      });
    });
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    // Override /me to return 401
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({ status: 401 });
    });

    await page.goto('/dashboard');
    // Should redirect to login
    await expect(page).toHaveURL('/login');
  });

  test.describe('Authenticated', () => {
    test.beforeEach(async ({ context }) => {
      await context.addInitScript(() => {
        window.localStorage.setItem('auth_token', 'mock-jwt-token');
      });
    });

    test('should navigate between main pages', async ({ page }) => {
      // Dashboard
      await page.goto('/dashboard');
      await expect(page).toHaveURL('/dashboard');
      await expect(page.getByRole('heading', { name: 'Bom dia, Atleta!' }).or(page.getByRole('heading', { level: 1 }))).toBeVisible();

      // Chat
      await page.goto('/dashboard/chat');
      await expect(page).toHaveURL('/dashboard/chat');

      // Body
      await page.goto('/dashboard/body/weight');
      await expect(page).toHaveURL('/dashboard/body/weight');

      // Workouts
      await page.goto('/dashboard/workouts');
      await expect(page).toHaveURL('/dashboard/workouts');

      // Settings
      await page.goto('/dashboard/settings/profile');
      await expect(page).toHaveURL('/dashboard/settings/profile');
    });

    test('should redirect non-admin from /admin/users to home', async ({ page }) => {
      // Default user is role: 'user' from beforeEach
      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');

      // Non-admin should be redirected to dashboard
      await expect(page).toHaveURL('/dashboard');
    });

    test('should allow admin access to /admin/users', async ({ page }) => {
      // Override to return admin role
      await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ email: 'admin@example.com', role: 'admin', name: 'Admin', onboarding_completed: true }),
        });
      });

      // Mock admin users endpoint
      await page.route(/\/api\/admin\/users\//, async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ users: [], total: 0, page: 1, page_size: 20, total_pages: 0 }),
        });
      });

      await page.goto('/admin/users');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(700); // debounce

      await expect(page.getByRole('heading', { name: 'Gestão de Usuários' })).toBeVisible();
    });

    test('should use browser back button correctly', async ({ page }) => {
      await page.goto('/dashboard');
      await page.goto('/dashboard/chat');
      await page.goto('/dashboard/body/weight');

      // Go back
      await page.goBack();
      await expect(page).toHaveURL('/dashboard/chat');

      await page.goBack();
      await expect(page).toHaveURL('/dashboard');
    });
  });
});
