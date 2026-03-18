import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Chat Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should send a message and receive a trainer response', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/chat');
    await authenticatedPage.waitForLoadState('networkidle');
    
    const input = authenticatedPage.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 15000 });

    const userMessage = 'Qual é a minha meta de proteína de hoje?';
    await input.fill(userMessage);
    await authenticatedPage.locator('button[type="submit"]').click();

    // Check user message bubble
    await expect(authenticatedPage.getByText(userMessage).last()).toBeVisible({ timeout: 10000 });

    // Check trainer message bubble (AI response)
    // The init script in fixtures.ts mocks fetch to return "Eu sou seu treinador virtual."
    await expect(authenticatedPage.getByText(/treinador virtual/i).last()).toBeVisible({ timeout: 30000 });
  });

  test('should persist chat history', async ({ authenticatedPage, api }) => {
    // 1. Pre-seed history in VB
    const testMsg = 'Mensagem persistente de teste';
    await api.post('/message', { message: testMsg });
    
    // 2. Navigate to chat
    await authenticatedPage.goto('/dashboard/chat');
    
    // 3. Message should be there (fetched from /message/history)
    await expect(authenticatedPage.getByText(testMsg).first()).toBeVisible({ timeout: 20000 });
  });
});
