import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('AI Memories Feature', () => {
  test('creates, localizes, reloads, and deletes a normal-user memory', async ({
    authenticatedPage,
    ui,
    seedMemory,
  }) => {
    const memoryText = `E2E Test Memory ${Date.now()}`;

    await ui.navigateTo('settings');
    await authenticatedPage.getByRole('link', { name: t('settings.tabs.memories') }).click();
    await expect(authenticatedPage.getByText(t('memories.empty_title'))).toBeVisible({ timeout: 15000 });

    await seedMemory(memoryText);
    await authenticatedPage.reload({ waitUntil: 'networkidle' });

    const memoryCard = authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText });
    await expect(memoryCard).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(t('memories.title'))).toBeVisible();

    await authenticatedPage.evaluate(() => {
      window.localStorage.setItem('i18nextLng', 'es-ES');
    });
    await authenticatedPage.reload({ waitUntil: 'networkidle' });

    await expect(authenticatedPage.getByText(/Memorias AI/i)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Lo que la inteligencia sabe sobre ti/i)).toBeVisible({
      timeout: 15000,
    });
    await expect(authenticatedPage.getByText(memoryText)).toBeVisible({ timeout: 15000 });

    const localizedCard = authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText });
    const deleteBtn = localizedCard.getByTestId('btn-delete-memory');
    await deleteBtn.hover();
    await deleteBtn.click();
    await authenticatedPage.getByTestId('confirm-accept').click();
    await expect(authenticatedPage.getByTestId('toast-container')).toContainText(/Memor[ií]a (eliminada|removida)\./i);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByText(memoryText)).toHaveCount(0);
    await expect(authenticatedPage.getByText(/Aún no hay memorias capturadas\./i)).toBeVisible({
      timeout: 15000,
    });
  });
});
