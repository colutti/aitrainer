import { test, expect } from './fixtures';

test.describe('Memory Locale Rendering', () => {
  test('renders the same user memory, localizes it, and keeps a deleted memory absent after reload', async ({
    authenticatedPage,
    seedMemory,
  }) => {
    const memoryText = `E2E locale memory ${Date.now()}`;
    await seedMemory(memoryText);

    await authenticatedPage.goto('/dashboard/settings/memories');
    await expect(
      authenticatedPage
        .getByTestId('memories-list-screen')
        .getByRole('heading', { name: /AI Memories|Memórias AI|Memorias AI/i })
        .first()
    ).toBeVisible({
      timeout: 15000,
    });
    await expect(
      authenticatedPage.getByTestId('entity-list-screen').getByTestId('page-header-subtitle')
    ).toBeVisible({ timeout: 15000 });
    const memoryCard = authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText });
    await expect(memoryCard).toBeVisible({ timeout: 15000 });

    await authenticatedPage.evaluate(() => {
      window.localStorage.setItem('i18nextLng', 'es-ES');
    });
    await authenticatedPage.reload({ waitUntil: 'networkidle' });

    await expect(
      authenticatedPage
        .getByTestId('memories-list-screen')
        .getByRole('heading', { name: /Memorias AI/i })
        .first()
    ).toBeVisible({ timeout: 15000 });
    await expect(
      authenticatedPage.getByTestId('entity-list-screen').getByTestId('page-header-subtitle')
    ).toHaveText(/Lo que la inteligencia sabe sobre ti/i, { timeout: 15000 });
    await expect(memoryCard).toBeVisible({ timeout: 15000 });

    const deleteButton = memoryCard.getByTestId('btn-delete-memory');
    await deleteButton.hover();
    await deleteButton.click();
    await authenticatedPage.getByTestId('confirm-accept').click();
    await expect(authenticatedPage.getByTestId('toast-container')).toContainText(
      /Memor[ií]a (eliminada|removida)\./i,
    );

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText })).toHaveCount(0);
    await expect(
      authenticatedPage.getByText(/No memories captured yet\.|Nenhuma memória capturada ainda\.|Aún no hay memorias capturadas\./i)
    ).toBeVisible({ timeout: 15000 });
  });
});
