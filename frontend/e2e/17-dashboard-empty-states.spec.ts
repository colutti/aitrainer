import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test('dashboard empty states stay stable for a fresh user', async ({
  authenticatedPage,
  api,
}) => {
  await cleanupUserData(api);

  await authenticatedPage.goto('/dashboard');
  await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible();
  await expect(
    authenticatedPage.getByText(/histórico de volume indisponível/i)
  ).toBeVisible();
});
