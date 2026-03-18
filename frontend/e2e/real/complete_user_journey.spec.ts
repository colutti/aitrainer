import { test, expect } from '@playwright/test';

// Use a fresh browser context without persistent auth for this flow
test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Complete User Journey (E2E Automated)', () => {
  test.beforeEach(async ({ page }) => {
    // 1. Mock Backend API
    await page.route('**/api/**', async (route) => {
      const url = route.request().url();
      if (url.includes('/api/user/me')) {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ 
                email: 'e2e@example.com', 
                name: 'E2E User',
                role: 'user', 
                onboarding_completed: false, 
                subscription_plan: 'Free'
            })
        });
      } else if (url.includes('/api/user/login')) {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ token: 'mock-jwt-token' })
        });
      } else {
        await route.fulfill({ 
            status: 200, 
            contentType: 'application/json',
            body: JSON.stringify({ status: 'ok' }) 
        });
      }
    });

    // 2. Comprehensive Mock for Firebase
    const firebaseMockResponse = {
        kind: 'identitytoolkit#VerifyPasswordResponse',
        localId: 'mock-id',
        email: 'e2e@example.com',
        displayName: 'E2E User',
        idToken: 'mock-id-token',
        registered: true,
        refreshToken: 'mock-refresh-token',
        expiresIn: '3600',
        users: [{
            localId: 'mock-id',
            email: 'e2e@example.com',
            emailVerified: true
        }]
    };

    await page.route('https://identitytoolkit.googleapis.com/**', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(firebaseMockResponse)
        });
    });

    await page.route('https://securetoken.googleapis.com/**', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
                access_token: 'mock-token',
                expires_in: '3600',
                id_token: 'mock-id-token',
                user_id: 'mock-id'
            })
        });
    });
  });

  test('User can register and complete onboarding', async ({ page }) => {
    // Step 1: Register
    await page.goto('/login?mode=register&plan=free', { waitUntil: 'load' });
    
    await page.locator('input#email').fill('e2e@example.com');
    await page.locator('input#password').fill('Password123!');
    await page.locator('input#confirmPassword').fill('Password123!');
    
    console.log('Submitting Registration...');
    await page.locator('button[type="submit"]').click();

    // Step 2: Onboarding
    await page.waitForURL(/.*onboarding/, { timeout: 30000 });
    console.log('Arrived at onboarding!');

    // Mock completed status for subsequent checks
    await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ 
                email: 'e2e@example.com', 
                name: 'E2E User',
                role: 'user', 
                onboarding_completed: true, 
                subscription_plan: 'Free'
            })
        });
    });

    // Step 2 UI: Profile
    await page.getByRole('button', { name: /Masculino/i }).click();
    await page.locator('input#age').fill('30');
    await page.locator('input#weight').fill('80');
    await page.locator('input#height').fill('180');
    
    await page.getByRole('button', { name: /Próximo/i }).click();
    
    // Step 3: Plan
    await page.waitForTimeout(500);
    await page.getByRole('button', { name: /Próximo/i }).click();
    
    // Step 4: Trainer
    await page.waitForTimeout(500);
    await page.getByRole('button', { name: /Próximo/i }).click();

    // Step 5: Integrations -> Step 6 (Finish)
    await page.waitForTimeout(500);
    await page.getByRole('button', { name: /Finalizar/i }).click();
    
    // Final Step -> Dashboard
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: /Dashboard/i }).click();

    // Step 3: Final Verification
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 20000 });
    await expect(page.locator('#root')).toBeVisible();
    
    console.log('Test completed successfully!');
  });
});
