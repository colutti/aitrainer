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
    // We use a more specific locator for the card
    const brenoText = authenticatedPage.getByText(/Breno/i).first();
    await expect(brenoText).toBeVisible();
    
    // Verify Breno has the check icon (selected)
    const brenoCard = authenticatedPage.getByTestId('trainer-card-gymbro');
    await expect(brenoCard.getByTestId('check-icon')).toBeVisible();

    // Atlas should have the lock icon
    const atlasCard = authenticatedPage.getByTestId('trainer-card-atlas');
    await expect(atlasCard.locator('[data-testid="lock-icon"]').or(atlasCard.locator('.lucide-lock'))).toBeVisible();

    // Clicking Atlas should NOT change selection
    await atlasCard.click();
    await expect(brenoCard.getByTestId('check-icon')).toBeVisible();
    await expect(atlasCard.getByTestId('check-icon')).not.toBeVisible();
  });

  test('should show correct subscription info', async ({ authenticatedPage }) => {
    // Navigate to Settings first
    await authenticatedPage.goto('/dashboard/settings/profile');
    
    // Click "Assinatura" tab to ensure we are on the right page
    await authenticatedPage.locator('nav').getByText(/Assinatura/i).click();
    await authenticatedPage.waitForLoadState('networkidle');

    // The Free plan is localized to "Gratuito"
    // Use a simpler check for visibility
    await expect(authenticatedPage.getByText(/Gratuito/i).first()).toBeVisible();
    await expect(authenticatedPage.getByText(/Plano Atual/i).first()).toBeVisible();
    
    // Verify other plans are visible
    await expect(authenticatedPage.getByText(/Basic/i).first()).toBeVisible();
    await expect(authenticatedPage.getByText(/Pro/i).first()).toBeVisible();
  });
});
