import { test, expect } from '@playwright/test';

test.use({ storageState: { cookies: [], origins: [] } });

test.describe('Registration and Subscription Flow', () => {
  test.beforeEach(async ({ page }) => {
    // PROTECT BACKEND - Mock all API calls
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      const pathname = route.request().url();
      
      if (pathname.includes('/api/user/me')) {
        const auth = route.request().headers().authorization;
        if (!auth || auth === 'Bearer undefined') {
            await route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Not authenticated' }) });
        } else {
            await route.fulfill({
                status: 200,
                body: JSON.stringify({ id: '123', email: 'newuser@example.com', role: 'user', onboarding_completed: false })
            });
        }
      } else if (pathname.includes('/api/user/login')) {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ token: 'mock-jwt-token' })
        });
      } else if (pathname.includes('/api/stripe/create-checkout-session')) {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ url: 'https://checkout.stripe.com/mock-session' })
        });
      } else if (pathname.includes('/api/onboarding/profile')) {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ status: 'success', token: 'mock-new-auth-token' })
        });
      } else {
        await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${pathname}` }) });
      }
    });

    // Mock Google Identity Toolkit (Firebase Auth)
    await page.route('https://identitytoolkit.googleapis.com/v1/accounts:*', async (route) => {
      const url = route.request().url();
      if (url.includes(':lookup')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            kind: "identitytoolkit#GetAccountInfoResponse",
            users: [{
              localId: 'mock-local-id',
              email: 'newuser@example.com',
              emailVerified: true,
              lastLoginAt: '123456789',
              createdAt: '123456789'
            }]
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            kind: "identitytoolkit#SignupNewUserResponse",
            localId: 'mock-local-id',
            email: 'newuser@example.com',
            displayName: 'Test User',
            registered: true,
            idToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtb2NrLWxvY2FsLWlkIiwiZW1haWwiOiJuZXd1c2VyQGV4YW1wbGUuY29tIn0.signature',
            refreshToken: 'mock-refresh-token',
            expiresIn: '3600'
          })
        });
      }
    });
  });

  test('should go from pricing to stripe checkout after registration', async ({ page }) => {
    // 1. Start at Landing Page directly at Pricing
    await page.goto('/#planos', { waitUntil: 'networkidle' });
    
    // 2. Click Pro plan button
    const proButton = page.getByTestId('plan-button-pro');
    
    await expect(proButton).toBeVisible({ timeout: 15000 });
    await proButton.click({ force: true });

    // 3. Verify we are on Register page with plan=pro
    await expect(page).toHaveURL(/\/login\?mode=register&plan=pro/);

    // 4. Fill registration form
    await page.locator('input[type="email"]').fill('newuser@example.com');
    await page.locator('input[type="password"]').nth(0).fill('Password123');
    await page.locator('input[type="password"]').nth(1).fill('Password123');

    // 5. Submit registration
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click({ force: true });

    // 6. Verify we are redirected to Stripe
    await page.waitForURL(/.*checkout\.stripe\.com.*/, { timeout: 30000 });
    expect(page.url()).toContain('checkout.stripe.com');
  });

  test('should skip stripe for free plan and go to onboarding', async ({ page }) => {
    // 1. Start at Landing Page
    await page.goto('/#planos', { waitUntil: 'networkidle' });
    
    // 2. Click Free plan button
    const freeButton = page.getByTestId('plan-button-free');
    
    await expect(freeButton).toBeVisible({ timeout: 15000 });
    await freeButton.click({ force: true });

    // 3. Verify we are on Register page
    await expect(page).toHaveURL(/\/login\?mode=register/);

    // 4. Fill registration form
    await page.locator('input[type="email"]').fill('freeuser@example.com');
    await page.locator('input[type="password"]').nth(0).fill('Password123');
    await page.locator('input[type="password"]').nth(1).fill('Password123');
    
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click({ force: true });

    await page.waitForURL(/.*onboarding.*/, { timeout: 20000 });
    
    // --- START ONBOARDING STEPS ---
    
    // Step 2: Profile
    await expect(page.locator('h2')).toContainText(/Perfil|Profile|Diga-nos/i, { timeout: 15000 });
    await page.getByRole('button').filter({ hasText: /Masculino|Male/i }).first().click();
    await page.locator('input#age').fill('30');
    await page.locator('input#weight').fill('85');
    await page.locator('input#height').fill('180');
    await page.getByRole('button').filter({ hasText: /Próximo|Next/i }).click();

    // Step 3: Plan
    await expect(page.locator('h2')).toContainText(/Plano|Plan/i, { timeout: 10000 });
    await page.getByRole('button').filter({ hasText: /Próximo|Next/i }).click();

    // Step 4: Trainer
    await expect(page.locator('h2')).toContainText(/Treinador|Trainer/i, { timeout: 10000 });
    await page.getByRole('button').filter({ hasText: /GymBro/i }).first().click();
    await page.getByRole('button').filter({ hasText: /Próximo|Next/i }).click();

    // Step 5: Integrations
    await expect(page.locator('h2')).toContainText(/Turbine|Integrations/i, { timeout: 15000 });
    await page.getByRole('button').filter({ hasText: /Finalizar|Finish/i }).click();

    // Success
    await expect(page.locator('h1')).toContainText(/Pronto|Sucesso|Ready|Success/i, { timeout: 15000 });
    const dashboardBtn = page.getByRole('button').filter({ hasText: /Dashboard/i });
    await expect(dashboardBtn).toBeVisible();
    await dashboardBtn.click();
    await page.waitForURL(/.*dashboard.*/);
  });

  test('should show success message after returning from stripe with payment=success', async ({ page }) => {
    // 1. Mock user as authenticated but with pending payment success
    await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({
                id: '123',
                email: 'test@example.com',
                display_name: 'Test User',
                subscription_plan: 'Pro',
                onboarding_completed: true
            })
        });
    });

    // 2. Set fake token in localStorage before navigation
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });

    // 3. Go to dashboard with success param
    await page.goto('/dashboard?payment=success', { waitUntil: 'networkidle' });

    // Handle Dashboard Tour if it appears
    const skipTourBtn = page.getByRole('button', { name: /Pular Tour|Skip Tour/i });
    if (await skipTourBtn.isVisible()) {
        await skipTourBtn.click();
    }

    // 4. Verify success param is removed (proves the logic ran)
    await expect(page).not.toHaveURL(/.*payment=success.*/, { timeout: 15000 });

    // 5. Check if toast is present
    await expect(page.locator('body')).toContainText(/sucesso|success/i, { timeout: 15000 });
  });

  test('should handle payment cancellation gracefully', async ({ page }) => {
    // 1. Mock auth as completed
    await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ id: '123', email: 'user@example.com', role: 'user', onboarding_completed: true })
        });
    });
    
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });

    // 2. Go to dashboard with cancelled param
    await page.goto('/dashboard?payment=cancelled', { waitUntil: 'networkidle' });

    // 3. Verify warning/info notification
    await expect(page.locator('body')).toContainText(/cancelado|interrompido|cancelled/i, { timeout: 15000 });
    
    // 4. Verify URL cleaned up
    await expect(page).not.toHaveURL(/.*payment=cancelled.*/, { timeout: 10000 });
  });

  test('should allow authenticated user to upgrade via Settings', async ({ page }) => {
    // 1. Mock user as Free
    await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ id: '123', email: 'user@example.com', role: 'user', subscription_plan: 'Free', onboarding_completed: true })
        });
    });
    
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });

    // 2. Go to Subscription page
    await page.goto('/dashboard/settings/subscription', { waitUntil: 'networkidle' });

    // Handle Dashboard Tour if it appears (sidebars might be blocked)
    const skipTourBtn = page.getByRole('button', { name: /Pular Tour|Skip Tour/i });
    if (await skipTourBtn.isVisible()) {
        await skipTourBtn.click();
    }

    // 3. Click to upgrade to Pro using data-testid
    const proUpgradeBtn = page.getByTestId('subscription-plan-btn-pro');
    await expect(proUpgradeBtn).toBeVisible({ timeout: 15000 });
    await proUpgradeBtn.click();

    // 4. Verify Stripe redirect
    await page.waitForURL(/.*checkout\.stripe\.com.*/, { timeout: 20000 });
  });

  test('should enforce validation rules in onboarding', async ({ page }) => {
    // 1. Authenticated user needing onboarding
    await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ id: '123', email: 'user@example.com', role: 'user', onboarding_completed: false })
        });
    });
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });

    await page.goto('/onboarding', { waitUntil: 'networkidle' });

    // Step 2 profile: try to proceed with empty/invalid data
    const nextBtn = page.getByRole('button').filter({ hasText: /Próximo|Next/i });
    await expect(nextBtn).toBeDisabled();

    // Fill partially
    await page.locator('input#age').fill('15'); // Too young maybe? Check logic
    await page.locator('input#weight').fill('50');
    await expect(nextBtn).toBeDisabled(); // Assuming age >= 18 is required

    await page.locator('input#age').fill('25');
    await page.locator('input#height').fill('175');
    // Gender still missing
    await expect(nextBtn).toBeDisabled();
    
    await page.getByRole('button').filter({ hasText: /Masculino|Male/i }).first().click();
    await expect(nextBtn).toBeEnabled();
  });

  test('should lock/unlock trainers based on plan selection in onboarding', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });
    await page.goto('/onboarding', { waitUntil: 'networkidle' });

    // Step 2: Skip to Step 3 (Plan)
    await page.getByRole('button').filter({ hasText: /Masculino|Male/i }).first().click();
    await page.locator('input#age').fill('25');
    await page.locator('input#weight').fill('70');
    await page.locator('input#height').fill('170');
    await page.getByRole('button').filter({ hasText: /Próximo|Next/i }).click();

    // Step 3: Choose Free Plan
    await expect(page.locator('h2')).toContainText(/Plano|Plan/i);
    await page.getByText(/Free/i).first().click();
    await page.getByRole('button').filter({ hasText: /Próximo|Next/i }).click();

    // Step 4: Verify only GymBro is available
    await expect(page.locator('h2')).toContainText(/Treinador|Trainer/i);
    const atlasBtn = page.getByRole('button').filter({ hasText: /Atlas/i });
    await expect(atlasBtn).toBeDisabled();
    
    const gymBroBtn = page.getByRole('button').filter({ hasText: /GymBro/i });
    await expect(gymBroBtn).toBeEnabled();

    // Go back and change to Pro
    await page.getByRole('button').filter({ hasText: /Voltar|Back/i }).click();
    await page.getByText(/Pro/i).first().click();
    await page.getByRole('button').filter({ hasText: /Próximo|Next/i }).click();

    // Verify Atlas is now available
    await expect(atlasBtn).toBeEnabled();
  });

  test('should resume onboarding if user returns before finishing', async ({ page }) => {
    // 1. Mock user as "not completed onboarding"
    await page.route('**/api/user/me', async (route) => {
        await route.fulfill({
            status: 200,
            body: JSON.stringify({ id: '123', email: 'resume@example.com', role: 'user', onboarding_completed: false })
        });
    });
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });

    // 2. Go to dashboard (should be redirected to onboarding)
    await page.goto('/dashboard', { waitUntil: 'networkidle' });
    await page.waitForURL(/.*onboarding.*/, { timeout: 10000 });
    
    // 3. Verify we are at step 2 (Profile)
    await expect(page.locator('h2')).toContainText(/Perfil|Profile|Diga-nos/i);
  });

  test('should preserve data when going back in onboarding steps', async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt-token');
    });
    await page.goto('/onboarding', { waitUntil: 'networkidle' });

    // 1. Fill Step 2 (Profile)
    await page.getByRole('button').filter({ hasText: /Feminino|Female/i }).first().click();
    await page.locator('input#age').fill('32');
    await page.locator('input#weight').fill('65');
    await page.locator('input#height').fill('168');
    
    const nextBtn = page.getByRole('button').filter({ hasText: /Próximo|Next/i });
    await nextBtn.click();

    // 2. We should be at Step 3 (Plan)
    await expect(page.locator('h2')).toContainText(/Plano|Plan/i);

    // 3. Go back
    await page.getByRole('button').filter({ hasText: /Voltar|Back/i }).click();

    // 4. Verify data is still there
    await expect(page.locator('input#age')).toHaveValue('32');
    await expect(page.locator('input#weight')).toHaveValue('65');
    await expect(page.locator('input#height')).toHaveValue('168');
    // Check if the feminine button is still "active" (usually has a specific class or border)
    // For now, checking inputs is a very strong proof of state persistence.
  });
});
