import { test, expect } from './fixtures';

test.describe('Navigation Flow', () => {

  test('should navigate correctly via Sidebar on Desktop', async ({ authenticatedPage }) => {
    // 1440px is desktop (lg:flex in Tailwind)
    await authenticatedPage.setViewportSize({ width: 1440, height: 900 });
    await authenticatedPage.goto('/dashboard');

    const sidebar = authenticatedPage.locator('aside');
    await expect(sidebar).toBeVisible();

    // Verify all major links are present and working
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
      await sidebar.getByText(item.text).click();
      await expect(authenticatedPage).toHaveURL(item.url);
      
      if (item.text !== 'Início') {
        await sidebar.getByText('Início').click();
        await expect(authenticatedPage).toHaveURL(/\/dashboard$/);
      }
    }
  });

  test('should navigate correctly via BottomNav on Mobile', async ({ authenticatedPage }) => {
    // 375px is mobile
    await authenticatedPage.setViewportSize({ width: 375, height: 667 });
    await authenticatedPage.goto('/dashboard');

    // Sidebar should be hidden
    await expect(authenticatedPage.locator('aside')).not.toBeVisible();

    // Bottom nav should be visible
    const bottomNav = authenticatedPage.locator('nav').filter({ has: authenticatedPage.locator('[data-testid="nav-home"]') }).last();
    await expect(bottomNav).toBeVisible();

    // Verify bottom nav items using testId
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
      await authenticatedPage.locator(`[data-testid="${item.testId}"]`).click();
      await expect(authenticatedPage).toHaveURL(item.url);
    }
  });

  test('should show correct subscription badge and message limits in Sidebar', async ({ authenticatedPage, api }) => {
    await authenticatedPage.setViewportSize({ width: 1440, height: 900 });
    
    // Ensure user is Free
    await api.post('/stripe/webhook', {
      type: 'customer.subscription.deleted',
      data: {
        object: {
          customer: 'cus_E2E_BOT_ID',
          metadata: { user_email: 'e2e-bot@fityq.it' }
        }
      }
    });

    await authenticatedPage.goto('/dashboard');
    const sidebar = authenticatedPage.locator('aside');
    
    await expect(sidebar.getByText('FREE')).toBeVisible();
    await expect(sidebar.getByText(/MSGS/)).toBeVisible();
  });
});
