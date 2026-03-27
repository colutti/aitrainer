import { test, expect } from './fixtures';

test('settings survives a hard reload on the profile tab', async ({
  authenticatedPage,
}) => {
  await authenticatedPage.goto('/dashboard/settings/profile');
  await expect(authenticatedPage.getByTestId('profile-form')).toBeVisible();

  await authenticatedPage.reload();

  await expect(authenticatedPage.getByTestId('profile-form')).toBeVisible();
});
