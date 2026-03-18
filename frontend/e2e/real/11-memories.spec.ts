import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Memories Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should list and delete AI insights (memories)', async ({ authenticatedPage, api }) => {
    // 1. Seed memories
    await api.post('/memory', {
      memory: 'O usuário prefere treinar peito'
    });
    
    await authenticatedPage.goto('/dashboard/settings/memories');
    await authenticatedPage.waitForLoadState('networkidle');

    // 2. Check if memory is listed
    const card = authenticatedPage.locator('div.bg-dark-card').filter({ hasText: /prefere treinar peito/i }).first();
    await expect(card).toBeVisible({ timeout: 15000 });

    // 3. Delete memory
    // Hover to trigger visibility (best practice)
    await card.hover();
    
    // Use a very generic but effective locator for the delete button inside this card
    const deleteBtn = card.locator('button').last();
    await deleteBtn.click({ force: true });
    
    // Confirm in modal - looking for button with "Excluir" or "Confirmar" or "Sim"
    const confirmBtn = authenticatedPage.locator('button').filter({ hasText: /Excluir|Confirmar|Sim/i }).last();
    await expect(confirmBtn).toBeVisible({ timeout: 5000 });
    await confirmBtn.click({ force: true });

    // 4. Verify gone
    await expect(authenticatedPage.getByText(/prefere treinar peito/i)).not.toBeVisible({ timeout: 15000 });
  });
});
