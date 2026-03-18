import { test, expect } from './fixtures';

test.describe('Navigation Flow', () => {

  test('should navigate correctly via Sidebar on Desktop', async ({ authenticatedPage }) => {
    await authenticatedPage.setViewportSize({ width: 1440, height: 900 });
    await authenticatedPage.goto('/dashboard');

    const sidebar = authenticatedPage.locator('aside');
    await expect(sidebar).toBeVisible({ timeout: 15000 });

    const navItems = [
      { text: 'Início', url: /\/dashboard$/ },
      { text: 'Treinador', url: /.*chat/ },
      { text: 'Meus Treinos', url: /.*workouts/ },
      { text: 'Peso e Corpo', url: /.*body\/weight/ },
      { text: 'Dieta e Macros', url: /.*body\/nutrition/ },
      { text: 'Configurações', url: /.*settings/ },
    ];

    for (const item of navItems) {
      console.log(`Testing navigation to: ${item.text}`);
      const link = sidebar.locator('a, button').filter({ hasText: new RegExp(`^${item.text}$`, 'i') }).first();
      await link.click({ force: true });
      await expect(authenticatedPage).toHaveURL(item.url, { timeout: 15000 });
      
      if (!authenticatedPage.url().endsWith('/dashboard')) {
        const homeLink = sidebar.locator('a, button').filter({ hasText: /Início/i }).first();
        await homeLink.click({ force: true });
        await expect(authenticatedPage).toHaveURL(/\/dashboard$/, { timeout: 15000 });
      }
    }
  });

  test('should navigate correctly via BottomNav on Mobile', async ({ authenticatedPage }) => {
    await authenticatedPage.setViewportSize({ width: 375, height: 667 });
    await authenticatedPage.goto('/dashboard');

    const bottomNav = authenticatedPage.locator('nav').filter({ has: authenticatedPage.locator('[data-testid="nav-home"]') }).last();
    await expect(bottomNav).toBeVisible({ timeout: 15000 });

    const mobileItems = [
      { testId: 'nav-home', url: /\/dashboard$/ },
      { testId: 'nav-chat', url: /.*chat/ },
      { testId: 'nav-workouts', url: /.*workouts/ },
      { testId: 'nav-body', url: /.*body\/weight/ },
      { testId: 'nav-nutrition', url: /.*body\/nutrition/ },
      { testId: 'nav-settings', url: /.*settings/ },
    ];

    for (const item of mobileItems) {
      console.log(`Testing mobile navigation to testId: ${item.testId}`);
      await authenticatedPage.locator(`[data-testid="${item.testId}"]`).click({ force: true });
      await expect(authenticatedPage).toHaveURL(item.url, { timeout: 15000 });
    }
  });

  test('should show correct subscription badge and message limits in Sidebar', async ({ authenticatedPage, api }) => {
    await authenticatedPage.setViewportSize({ width: 1440, height: 900 });
    
    // Ensure user is Free
    await api.post('/stripe/webhook', {
      type: 'customer.subscription.deleted',
      data: { object: { metadata: { user_email: 'e2e-bot@fityq.it' } } }
    });

    await authenticatedPage.goto('/dashboard');
    const sidebar = authenticatedPage.locator('aside');
    
    // Check for "Free" or "Gratuito" depending on i18n
    await expect(sidebar.getByText(/Free|Gratuito/i).first()).toBeVisible({ timeout: 15000 });
    
    // Check for message limit label (the static part)
    const msgsLabel = authenticatedPage.locator('aside').getByText(/Mensagens|Msgs/i).first();
    await expect(msgsLabel).toBeVisible({ timeout: 15000 });
    
    // Check for the limit numbers (e.g. "5" and "10")
    await expect(authenticatedPage.locator('aside').getByText('5').first()).toBeVisible();
    await expect(authenticatedPage.locator('aside').getByText('/ 10').first()).toBeVisible();
  });
});
