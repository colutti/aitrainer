import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('AI Memories Feature', () => {
  test('should list and delete an AI memory', async ({ authenticatedPage, ui, seedMemory }) => {
    authenticatedPage.on('console', msg => console.log('PAGE LOG:', msg.text()));
    authenticatedPage.on('pageerror', err => console.log('PAGE ERROR:', err.message));

    // 1. Seed a unique memory
    const memoryText = `E2E Test Memory ${Math.random()}`;
    await seedMemory(memoryText);

    // 2. Navigate to Memories via SPA navigation
    await ui.navigateTo('settings');
    const memoriesTab = authenticatedPage.getByRole('link', { name: t('settings.tabs.memories') });
    await memoriesTab.click();

    // 3. Verify Memory is in list
    // Use a robust wait for the API to load the memory
    const memoryCard = authenticatedPage.getByTestId('memory-card').filter({ hasText: memoryText });
    
    try {
      await expect(memoryCard).toBeVisible({ timeout: 15000 });
    } catch (e) {
      console.log('QA Diagnostic: Memories Page HTML Dump:', await authenticatedPage.innerHTML('.flex-1.min-h-\\[500px\\]'));
      throw e;
    }

    // 4. Click Delete
    const deleteBtn = memoryCard.getByTestId('btn-delete-memory');
    // On desktop it might be hidden until hover, but Playwright click() should handle it or we hover
    await deleteBtn.hover();
    await deleteBtn.click();

    // 5. Confirm Deletion in Modal
    const confirmBtn = authenticatedPage.getByTestId('confirm-accept');
    await confirmBtn.click();

    // 6. Verify Memory is removed
    await expect(memoryCard).toBeHidden({ timeout: 10000 });
    
    // 7. Success Toast
    await ui.waitForToast('memories.delete_success');
  });
});
