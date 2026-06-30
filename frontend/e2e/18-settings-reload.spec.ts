import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test('persists profile edits across a reload', async ({ authenticatedPage, ui }) => {
  await authenticatedPage.goto('/dashboard/settings/profile');
  await expect(authenticatedPage.getByTestId('profile-form')).toBeVisible({ timeout: 15000 });

  const newName = `Reloaded User ${Date.now()}`;
  const genderSelect = authenticatedPage.getByLabel(t('common.gender'));
  await authenticatedPage.getByTestId('profile-name').fill(newName);
  await genderSelect.selectOption({ label: t('onboarding.genders.female') });
  await authenticatedPage.getByTestId('profile-age').fill('34');
  await authenticatedPage.getByTestId('profile-height').fill('172');
  await authenticatedPage.getByRole('button', { name: t('common.save') }).click();
  await ui.waitForToast('settings.profile.save_success');

  await authenticatedPage.reload({ waitUntil: 'networkidle' });
  await expect(authenticatedPage.getByTestId('profile-name')).toHaveValue(newName);
  await expect(genderSelect).toHaveValue(t('onboarding.genders.female'));
  await expect(authenticatedPage.getByTestId('profile-age')).toHaveValue('34');
  await expect(authenticatedPage.getByTestId('profile-height')).toHaveValue('172');
  await expect(authenticatedPage.getByTestId('profile-header-name')).toContainText(newName);
});
