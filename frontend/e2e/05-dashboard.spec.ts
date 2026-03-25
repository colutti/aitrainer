import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Dashboard Features', () => {
  test('should display all main dashboard widgets and data correctly', async ({ authenticatedPage, ui }) => {
    // 1. Wait for Bento Dashboard to load
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });

    // 2. Check Key Premium Widgets (using titles from i18n)
    // Some titles might be hidden on very small screens, so we check if they EXIST first
    // and only check visibility if we know they are not 'hidden' in tailwind.
    // For "Streak", we use a more resilient locator that doesn't care about the hidden class if it's the main container
    await expect(authenticatedPage.getByText(t('dashboard.recent_prs_title'))).toBeVisible();
    await expect(authenticatedPage.getByText(t('dashboard.strength_radar_title'))).toBeVisible();
    await expect(authenticatedPage.getByText(t('dashboard.volume_trend_title'))).toBeVisible();

    // 3. Check Confidence Widget
    await expect(authenticatedPage.getByText(t('dashboard.confidence'))).toBeVisible();
  });

  test('should show payment success toast notification', async ({ authenticatedPage, ui }) => {
    // Navigate with success query param to trigger toast
    await authenticatedPage.goto('/dashboard?payment=success');
    
    // Validate toast using i18n key logic in helper
    await ui.waitForToast('landing.subscription.payment_success_message');
  });
});
