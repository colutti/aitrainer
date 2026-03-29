import { test, expect } from './fixtures';

test('dashboard empty states stay stable for a fresh user', async ({
  authenticatedPage,
}) => {
  await authenticatedPage.goto('/dashboard');
  await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible();
  await expect(
    authenticatedPage.getByText(/histórico de volume indisponível/i)
  ).toBeVisible();

  await authenticatedPage.reload({ waitUntil: 'networkidle' });
  await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible();
});
