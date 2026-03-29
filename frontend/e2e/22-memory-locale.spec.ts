import { test, expect } from './fixtures';

test.describe('Memory Locale Rendering', () => {
  test('renders the same user memory while switching the interface locale', async ({
    authenticatedPage,
    seedMemory,
  }) => {
    const memoryText = `E2E locale memory ${Date.now()}`;
    await seedMemory(memoryText);

    await authenticatedPage.goto('/dashboard/settings/memories');
    await expect(authenticatedPage.getByText(/AI Memories|Memórias AI|Memorias AI/i)).toBeVisible({
      timeout: 15000,
    });
    await expect(
      authenticatedPage.getByText(
        /What the intelligence knows about you|O que a inteligência sabe sobre você|Lo que la inteligencia sabe sobre ti/i,
      )
    ).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(memoryText)).toBeVisible({ timeout: 15000 });

    await authenticatedPage.evaluate(() => {
      window.localStorage.setItem('i18nextLng', 'es-ES');
    });
    await authenticatedPage.reload({ waitUntil: 'networkidle' });

    await expect(authenticatedPage.getByText(/Memorias AI/i)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Lo que la inteligencia sabe sobre ti/i)).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(memoryText)).toBeVisible({ timeout: 15000 });
  });
});
