import { test, expect } from '@playwright/test';

test.describe('Admin Users Feature Debug', () => {
  test('debug navigation', async ({ page, context }) => {
    page.on('console', msg => console.log('[Browser Console]', msg.type(), msg.text()));
    page.on('request', request => console.log('[All Requests]', request.method(), request.url()));

    await page.route('**/*', async (route) => {
      const url = route.request().url();
      if (url.includes('admin') || url.includes('user') || url.includes('8001')) {
        console.log('[INTERCEPTED]', url);
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ email: 'admin@ex.com', role: 'admin', name: 'Admin', users: [], total: 0, page: 1, total_pages: 0 })
        });
      }
      return route.continue();
    });

    await context.addInitScript(() => {
      window.localStorage.setItem('admin_auth_token', 'mock-token');
    });

    await page.goto('http://localhost:3001/users');
    await page.waitForLoadState('networkidle');
    
    console.log('Page Title:', await page.title());
    console.log('Page Content snippet:', (await page.content()).slice(0, 500));
    
    // Check if we see the login page or the users page
    const loginText = page.getByText('ENTRAR NO PAINEL');
    const usersHeader = page.getByText('Gestão de Usuários');
    
    if (await loginText.isVisible()) {
        console.log('WE ARE ON THE LOGIN PAGE');
    } else if (await usersHeader.isVisible()) {
        console.log('WE ARE ON THE USERS PAGE');
    } else {
        console.log('WE ARE SOMEWHERE ELSE');
    }
  });
});
