import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Chat Feature', () => {
  test('should send a message, receive a response, and persist after reload', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('chat');

    const messageInput = authenticatedPage.getByPlaceholder(t('chat.input_placeholder'));
    await expect(messageInput).toBeVisible({ timeout: 15000 });

    const uniqueMessage = `Hello from Playwright E2E ${Date.now()}`;
    await messageInput.fill(uniqueMessage);
    await authenticatedPage.keyboard.press('Enter');

    await expect(authenticatedPage.getByText(uniqueMessage)).toBeVisible({ timeout: 10000 });

    const aiResponse = authenticatedPage.locator('[data-testid="chat-message"]:not(.flex-row-reverse)').last();
    await expect(aiResponse).toBeVisible({ timeout: 45000 });
    await expect(messageInput).toBeEnabled({ timeout: 45000 });

    const aiText = (await aiResponse.locator('.prose').innerText()).replace(/\s+/g, ' ').trim();
    expect(aiText.length).toBeGreaterThan(5);
    expect(aiText).not.toContain(uniqueMessage);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/chat');
    await expect(authenticatedPage.getByTestId('chat-form')).toBeVisible({ timeout: 15000 });
    const restoredAiResponse = authenticatedPage.locator('[data-testid="chat-message"]:not(.flex-row-reverse)').last();
    await expect(restoredAiResponse).toBeVisible({ timeout: 45000 });
    await expect(restoredAiResponse.locator('.prose')).toContainText(aiText);
  });
});
