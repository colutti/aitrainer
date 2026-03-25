import { test, expect } from '@playwright/test';

// Ensure we start without session for auth guard tests
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Auth Guards & Protected Routes', () => {
  const protectedRoutes = [
    '/dashboard',
    '/dashboard/workouts',
    '/dashboard/body',
    '/dashboard/chat',
    '/dashboard/settings',
    '/dashboard/settings/profile',
    '/dashboard/settings/subscription',
    '/onboarding'
  ];

  for (const route of protectedRoutes) {
    test(`should redirect unauthenticated user from ${route} to login`, async ({ page }) => {
      await page.goto(route);
      
      // Should be redirected to login
      await expect(page).toHaveURL(/\/login/);
      
      // Should preserve the intended destination in the state (if implemented)
      // or at least show the login page
      const loginTitle = page.getByRole('heading', { level: 1 });
      await expect(loginTitle).toContainText(/FITYQ/i);
    });
  }
});
