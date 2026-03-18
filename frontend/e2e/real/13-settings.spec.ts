import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('General Settings', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should verify trainer is locked to Breno for Free users', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/trainer');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Check initial trainer (Breno should be selected and forced for Free user)
    const brenoText = authenticatedPage.getByText(/Breno/i).first();
    await expect(brenoText).toBeVisible({ timeout: 15000 });
    
    // Verify Breno has the check icon (selected)
    const brenoCard = authenticatedPage.getByTestId('trainer-card-gymbro').first();
    await expect(brenoCard.getByTestId('check-icon')).toBeVisible({ timeout: 10000 });

    // Atlas should have the lock icon
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas').first();
    await expect(atlasCard.locator('[data-testid="lock-icon"]').or(atlasCard.locator('.lucide-lock'))).toBeVisible({ timeout: 10000 });

    // Clicking Atlas should NOT change selection
    await atlasCard.click();
    await expect(brenoCard.getByTestId('check-icon')).toBeVisible({ timeout: 10000 });
    await expect(atlasCard.getByTestId('check-icon')).not.toBeVisible({ timeout: 10000 });
  });

  test('should show correct subscription info', async ({ authenticatedPage }) => {
    // Navigate to Settings profile
    await authenticatedPage.goto('/dashboard/settings/profile');
    
    // Click "Assinatura" tab to ensure we are on the right page
    const subscriptionTab = authenticatedPage.locator('nav').getByText(/Assinatura/i).first();
    await subscriptionTab.click();
    await authenticatedPage.waitForLoadState('networkidle');

    // The Free plan is localized to "Gratuito"
    await expect(authenticatedPage.getByText(/Gratuito/i).first()).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Plano Atual/i).first()).toBeVisible({ timeout: 10000 });
    
    // Verify other plans are visible
    await expect(authenticatedPage.getByText(/Basic/i).first()).toBeVisible({ timeout: 10000 });
    await expect(authenticatedPage.getByText(/Pro/i).first()).toBeVisible({ timeout: 10000 });
  });
});
