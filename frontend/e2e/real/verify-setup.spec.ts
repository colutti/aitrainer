import { test, expect } from './fixtures';

test.describe('Real E2E Setup Verification', () => {
  test('should be able to reach dashboard and calling API via fixture', async ({ authenticatedPage, api }) => {
    authenticatedPage.on('console', msg => console.log('PAGE LOG:', msg.text()));
    
    // 1. Verify page is on dashboard
    await authenticatedPage.goto('/dashboard', { waitUntil: 'networkidle' });
    await expect(authenticatedPage).toHaveURL(/.*dashboard/);
    
    // 2. Verify API fixture works
    const res = await api.get('/user/me');
    expect(res.status()).toBe(200);
    const user = await res.json();
    console.log('Current E2E user:', user.email);
    expect(user.email).toBeDefined();
  });
});
