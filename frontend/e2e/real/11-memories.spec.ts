import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Memories Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should list and delete AI insights (memories)', async ({ authenticatedPage, api }) => {
    // 1. Seed memories via newly added POST endpoint
    await api.post('/memory', {
      memory: 'O usuário prefere treinar peito às segundas-feiras.'
    });
    
    // Seed another one to test list multiple
    await api.post('/memory', {
      memory: 'O usuário está focando em hipertrofia.'
    });

    await authenticatedPage.goto('/dashboard/settings/memories');
    await authenticatedPage.waitForLoadState('networkidle');

    // 2. Check if memory is listed
    await expect(authenticatedPage.getByText('O usuário prefere treinar peito')).toBeVisible();

    // 3. Delete memory
    await authenticatedPage.locator('button:has-text("Excluir")').or(authenticatedPage.locator('.lucide-trash-2')).first().click();
    await authenticatedPage.locator('button:has-text("Confirmar")').click();

    // 4. Verify gone
    await expect(authenticatedPage.getByText('O usuário prefere treinar peito')).not.toBeVisible();
    await expect(authenticatedPage.getByText(/Nenhum insight/i)).toBeVisible();
  });
});
