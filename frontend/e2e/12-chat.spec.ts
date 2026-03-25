import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Chat Feature', () => {
  test('should load chat interface, send a message and receive response', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Chat
    await ui.navigateTo('chat');

    // 2. Wait for Chat Interface to be ready
    const messageInput = authenticatedPage.getByPlaceholder(t('chat.input_placeholder'));
    await expect(messageInput).toBeVisible({ timeout: 15000 });

    // 3. Send a Message
    const uniqueMessage = `Hello from Playwright E2E ${Date.now()}`;
    await messageInput.fill(uniqueMessage);
    await authenticatedPage.keyboard.press('Enter');

    // 4. Verify message appears in UI
    const sentMessage = authenticatedPage.getByText(uniqueMessage);
    await expect(sentMessage).toBeVisible({ timeout: 10000 });

    // 5. Verify AI response
    // We look for a message that is NOT aligned to the right (flex-row-reverse indicates user)
    const aiResponse = authenticatedPage.locator('[data-testid="chat-message"]:not(.flex-row-reverse)').last();
    await expect(aiResponse).toBeVisible({ timeout: 45000 });
    
    // Check that it's a real response
    const aiText = await aiResponse.innerText();
    expect(aiText.length).toBeGreaterThan(5);
    expect(aiText).not.toContain(uniqueMessage);
  });
});
