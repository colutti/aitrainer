import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Chat Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should send a message and receive a trainer response', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/chat');
    
    const input = authenticatedPage.locator('textarea');
    await expect(input).toBeVisible();

    const userMessage = 'Qual é a minha meta de proteína de hoje?';
    await input.fill(userMessage);
    await authenticatedPage.locator('button[type="submit"]').click();

    // Check user message bubble
    await expect(authenticatedPage.locator('[data-sender="user"]').last()).toContainText(userMessage);

    // Check trainer message bubble (AI response)
    // data-sender is 'trainer'
    const trainerMessage = authenticatedPage.locator('[data-sender="trainer"]').last();
    await expect(trainerMessage).toBeVisible({ timeout: 60000 });
  });

  test('should persist chat history between navigation', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/chat');
    
    await authenticatedPage.fill('textarea', 'Esta é uma mensagem de teste para persistência.');
    await authenticatedPage.click('button[type="submit"]');
    
    // Wait for it to appear
    await expect(authenticatedPage.locator('[data-sender="user"]').last()).toBeVisible();

    // Navigate away and back
    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.goto('/dashboard/chat');

    // Message should still be there
    await expect(authenticatedPage.getByText('Esta é uma mensagem de teste para persistência.')).toBeVisible();
  });
});
