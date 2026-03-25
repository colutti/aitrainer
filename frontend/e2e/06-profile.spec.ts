import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Profile Features (Self-Contained)', () => {
  test('should login and update user profile data', async ({ authenticatedPage, ui }) => {
    const page = authenticatedPage;

    // 1. Session is already active via fixture
    
    // 2. Navigate to Settings directly
    await page.goto('/dashboard/settings');
    
    // 3. Wait for Form to load (End of skeleton)
    const form = page.getByTestId('profile-form');
    await expect(form).toBeVisible({ timeout: 30000 });

    // 4. Update Identity and Physical Stats
    const newName = `E2E Bot ${Math.floor(Math.random() * 1000)}`;
    const newAge = 25 + Math.floor(Math.random() * 10);
    
    // Using fillForm (labels from pt-BR.json)
    await ui.fillForm({
      [t('settings.profile.name')]: newName,
      [t('common.age')]: newAge
    });

    // 6. Save
    await ui.submit();

    // 7. Validate Success Toast
    await ui.waitForToast('settings.profile.save_success');

    // 8. Verify UI Updated
    await expect(page.getByTestId('profile-header-name')).toContainText(newName);
    
    // Check if age updated in sidebar stats (this is in the model, so it should work)
    const ageDisplay = page.locator('p').filter({ hasText: String(newAge) });
    await expect(ageDisplay).toBeVisible();
  });
});
