import { test, expect } from './fixtures';

test.describe('App Core Flow', () => {

  test('should navigate and interact with chat correctly', async ({ authenticatedPage }) => {
    // Fixture already navigated to /dashboard with 1440x900 desktop viewport

    // 1. Dashboard Load - sidebar must be visible (desktop viewport)
    const sidebar = authenticatedPage.locator('aside').first();
    await expect(sidebar).toBeVisible({ timeout: 30000 });
    await expect(sidebar.locator('span', { hasText: 'FityQ' }).first()).toBeVisible({ timeout: 15000 });

    // Check main dashboard component
    await expect(authenticatedPage.getByText(/Meta Diária/i).first()).toBeVisible({ timeout: 15000 });

    // 2. Navigate to Chat via sidebar text link
    const trainerLink = authenticatedPage.locator('aside').getByText(/Treinador/i).first();
    await trainerLink.click();
    await expect(authenticatedPage).toHaveURL(/.*chat/, { timeout: 15000 });

    // 3. Chat interaction
    const input = authenticatedPage.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 15000 });

    const message = 'Olá treinador, como vai?';
    await input.fill(message);
    const submitBtn = authenticatedPage.locator('button[type="submit"]').first();
    await submitBtn.click();

    // Verify user message appears
    const userMsg = authenticatedPage.locator('[data-sender="user"]').first();
    await expect(userMsg).toContainText(message, { timeout: 15000 });

    // Wait for AI/trainer response (note: data-sender is 'trainer', not 'ai')
    const trainerMessage = authenticatedPage.locator('[data-sender="trainer"]').first();
    await expect(trainerMessage).toBeVisible({ timeout: 60000 });

    // 4. Navigate to Settings via sidebar text
    const settingsLink = authenticatedPage.locator('aside').getByText(/Configurações/i).first();
    await settingsLink.click();
    await expect(authenticatedPage).toHaveURL(/.*settings/, { timeout: 15000 });

    // 5. Back to Dashboard via sidebar text
    const homeLink = authenticatedPage.locator('aside').getByText(/Início/i).first();
    await homeLink.click();
    await expect(authenticatedPage).toHaveURL(/\/dashboard$/, { timeout: 15000 });
  });
});
