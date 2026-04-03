import { test, expect } from './fixtures';

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
    await expect(authenticatedPage.getByTestId('body-tab-weight')).toBeVisible({ timeout: 15000 });

    await authenticatedPage.getByTestId('body-tab-nutrition').click();
    await expect(authenticatedPage.getByRole('button', { name: /Registrar Refeição|Register Meal|Registrar Comida/i })).toBeVisible({ timeout: 15000 });

    await ui.navigateTo('body');
    await authenticatedPage.getByTestId('body-tab-weight').click();
    await authenticatedPage.getByRole('button', { name: /Registrar Peso|Register Weight|Registrar Peso/i }).click();
    await expect(authenticatedPage.getByRole('heading', { name: /Registrar Peso|Register Weight/i })).toBeVisible({
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
