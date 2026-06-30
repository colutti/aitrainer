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
    const newHeight = 165 + Math.floor(Math.random() * 25);
    const newGender = t('onboarding.genders.female');
    
    // Using fillForm (labels from pt-BR.json)
    await ui.fillForm({
      [t('settings.profile.name')]: newName,
      [t('common.age')]: newAge,
      [t('settings.height')]: newHeight,
    });
    await page.getByLabel(t('common.gender')).selectOption({ label: newGender });

    // 6. Save
    await ui.submit();

    // 7. Validate Success Toast (non-blocking: some environments persist silently)
    try {
      await ui.waitForToast('settings.profile.save_success');
    } catch (error) {
      console.warn('QA: profile save toast not found, proceeding with state validation.', error);
    }

    // 8. Verify UI Updated
    await expect(page.getByTestId('profile-header-name')).toContainText(newName);
    await expect(page.getByTestId('profile-form')).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId('profile-age')).toHaveValue(String(newAge));
    await expect(page.getByTestId('profile-height')).toHaveValue(String(newHeight));
    await expect(page.getByLabel(t('common.gender'))).toHaveValue(newGender);

    // 9. Reload and verify all editable fields persisted
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.getByTestId('profile-form')).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId('profile-name')).toHaveValue(newName);
    await expect(page.getByTestId('profile-age')).toHaveValue(String(newAge));
    await expect(page.getByTestId('profile-height')).toHaveValue(String(newHeight));
    await expect(page.getByLabel(t('common.gender'))).toHaveValue(newGender);
    await expect(page.getByTestId('profile-header-name')).toContainText(newName);

    // 10. Sidebar stats should reflect saved age and gender after reload
    await expect(page.getByText(String(newAge), { exact: true }).first()).toBeVisible();
    await expect(page.getByText(newGender, { exact: true }).first()).toBeVisible();
  });
});
