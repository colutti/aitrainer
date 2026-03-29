import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Mobile core navigation', () => {
  test('keeps navigation, tabs, drawers, and chat usable on a mobile viewport', async ({ authenticatedPage, ui }) => {
    await expect(authenticatedPage.getByTestId('desktop-nav')).toBeHidden({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('mobile-nav')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.locator('main').evaluate((main) => {
      if (main instanceof HTMLElement) {
        main.scrollTop = 9999;
      }
    });
    await expect(authenticatedPage.getByTestId('mobile-nav')).toBeVisible();

    await ui.navigateTo('body');
    await expect(authenticatedPage.getByRole('button', { name: t('body.weight_title') })).toBeVisible({ timeout: 15000 });

    await ui.switchToTab(t('body.nutrition_title'));
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('nutrition.history_title'));

    await ui.navigateTo('body');
    await ui.switchToTab(t('body.weight_title'));
    await ui.openDrawer(t('body.weight.register_weight'));
    await expect(authenticatedPage.getByRole('heading', { name: t('body.weight.register_weight') })).toBeVisible({
      timeout: 15000,
    });
    await expect(authenticatedPage.getByTestId('weight-kg')).toBeVisible();
    await ui.closeDrawer();

    await ui.navigateTo('chat');
    await expect(authenticatedPage.getByTestId('chat-form')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('chat-input')).toBeVisible({ timeout: 15000 });

    await ui.navigateTo('settings');
    await expect(authenticatedPage.getByTestId('profile-form')).toBeVisible({ timeout: 15000 });
  });
});
