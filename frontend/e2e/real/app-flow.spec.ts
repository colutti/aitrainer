import { test, expect } from './fixtures';

test.describe('App Core Flow', () => {

  test('should navigate and interact with chat correctly', async ({ authenticatedPage }) => {
    // Fixture already navigated to /dashboard with 1440x900 desktop viewport

    // 1. Dashboard Load - sidebar must be visible (desktop viewport)
    const sidebar = authenticatedPage.locator('aside');
    await expect(sidebar).toBeVisible({ timeout: 30000 });
    await expect(sidebar.locator('span', { hasText: 'FityQ' })).toBeVisible();

    // Check main dashboard component
    await expect(authenticatedPage.getByText(/Meta Di.ria/i)).toBeVisible();

    // 2. Navigate to Chat via sidebar text link
    await authenticatedPage.locator('aside').getByText('Treinador').click();
    await expect(authenticatedPage).toHaveURL(/.*chat/);

    // 3. Chat interaction
    const input = authenticatedPage.locator('textarea');
    await expect(input).toBeVisible({ timeout: 10000 });

    const message = 'Olá treinador, como vai?';
    await input.fill(message);
    await authenticatedPage.locator('button[type="submit"]').click();

    // Verify user message appears
    await expect(
      authenticatedPage.locator('[data-sender="user"]').last()
    ).toContainText(message, { timeout: 10000 });

    // Wait for AI/trainer response (note: data-sender is 'trainer', not 'ai')
    const trainerMessage = authenticatedPage.locator('[data-sender="trainer"]').last();
    await expect(trainerMessage).toBeVisible({ timeout: 60000 });

    // 4. Navigate to Settings via sidebar text
    await authenticatedPage.locator('aside').getByText('Configurações').click();
    await expect(authenticatedPage).toHaveURL(/.*settings/);

    // 5. Back to Dashboard via sidebar text
    await authenticatedPage.locator('aside').getByText('Início').click();
    await expect(authenticatedPage).toHaveURL(/\/dashboard$/);
  });
});
