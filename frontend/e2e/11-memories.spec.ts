import { test, expect } from './fixtures';
import { gotoAppRoute } from './helpers/bootstrap';

test.describe('AI Memories Feature', () => {
  test('creates, localizes, reloads, and deletes a normal-user memory', async ({
    authenticatedPage,
    ui,
    seedMemory,
  }) => {
    const memoryText = `E2E Test Memory ${Date.now()}`;

    await gotoAppRoute(authenticatedPage, '/dashboard/settings');
    await authenticatedPage.getByRole('link', { name: /Memories|Memórias|Memorias/i }).click();
    await expect(
      authenticatedPage.getByText(/No memories captured yet\.|Nenhuma memória capturada ainda\.|Aún no hay memorias capturadas\./i),
    ).toBeVisible({ timeout: 15000 });

    await seedMemory(memoryText);
    await authenticatedPage.reload({ waitUntil: 'commit' });

    const memoryCard = authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText });
    await expect(memoryCard).toBeVisible({ timeout: 15000 });
    await expect(
      authenticatedPage
        .getByTestId('memories-list-screen')
        .getByRole('heading', { name: /AI Memories|Memórias AI|Memorias AI/i })
        .first(),
    ).toBeVisible();

    await authenticatedPage.evaluate(() => {
      window.localStorage.setItem('i18nextLng', 'es-ES');
    });
    await authenticatedPage.reload({ waitUntil: 'commit' });

    await expect(
      authenticatedPage
        .getByTestId('memories-list-screen')
        .getByRole('heading', { name: /Memorias AI/i })
        .first(),
    ).toBeVisible({ timeout: 15000 });
    await expect(
      authenticatedPage.getByTestId('entity-list-screen').getByTestId('page-header-subtitle'),
    ).toHaveText(/Lo que la inteligencia sabe sobre ti/i, {
      timeout: 15000,
    });
    await expect(authenticatedPage.getByText(memoryText)).toBeVisible({ timeout: 15000 });

    const localizedCard = authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText });
    const deleteBtn = localizedCard.getByTestId('btn-delete-memory');
    await deleteBtn.hover();
    await deleteBtn.click();
    await authenticatedPage.getByTestId('confirm-accept').click();
    await expect(authenticatedPage.getByTestId('toast-container')).toContainText(/Memor[ií]a (eliminada|removida)\./i);

    await authenticatedPage.reload({ waitUntil: 'commit' });
    await expect(authenticatedPage.getByText(memoryText)).toHaveCount(0);
    await expect(
      authenticatedPage.getByText(/No memories captured yet\.|Nenhuma memória capturada ainda\.|Aún no hay memorias capturadas\./i),
    ).toBeVisible({
      timeout: 15000,
    });
  });
});
