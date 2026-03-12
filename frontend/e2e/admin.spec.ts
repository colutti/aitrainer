import { test, expect } from '@playwright/test';

const mockUsers = [
  { email: 'user1@ex.com', display_name: 'User One', is_admin: false, created_at: '2026-01-01T00:00:00Z', subscription_plan: 'Free' },
  { email: 'user2@ex.com', display_name: 'User Two', is_admin: false, created_at: '2026-01-15T00:00:00Z', subscription_plan: 'Basic' },
  { email: 'admin@ex.com', display_name: 'Admin User', is_admin: true, created_at: '2025-12-01T00:00:00Z', subscription_plan: 'Pro' },
];

const mockUsersResponse = {
  users: mockUsers,
  total: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

test.describe('Admin Users Feature', () => {
  test.beforeEach(async ({ context, page }) => {
    // page.on('console', msg => console.log('[Browser Console]', msg.type(), msg.text()));
    
    // Catch everything going to the backend port
    await context.route(url => url.toString().includes(':8001'), async (route) => {
      const url = route.request().url();
      const method = route.request().method();

      if (url.includes('/user/me')) {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ email: 'admin@ex.com', role: 'admin', name: 'Admin' })
        });
      }

      if (url.includes('/admin/users/')) {
        const detailMatch = /\/admin\/users\/([^?/]+)$/.exec(url);
        if (detailMatch && method === 'GET') {
          return route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              profile: mockUsers[0],
              stats: { message_count: 10, workout_count: 5, nutrition_count: 20 }
            })
          });
        }

        if (method === 'GET') {
           if (url.includes('search=user1')) {
             return route.fulfill({
               status: 200,
               contentType: 'application/json',
               body: JSON.stringify({ users: [mockUsers[0]], total: 1, page: 1, total_pages: 1 })
             });
           }
           return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(mockUsersResponse) });
        }
        
        if (method === 'DELETE') {
          return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) });
        }
      }
      
      await route.fulfill({ status: 200, body: JSON.stringify({}) });
    });

    await context.addInitScript(() => {
      window.localStorage.setItem('admin_auth_token', 'mock-jwt');
    });

    await page.goto('/users');
    await page.waitForLoadState('networkidle');
  });

  test('should display users list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Gestão de Usuários' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('user1@ex.com')).toBeVisible();
    await expect(page.getByText('admin@ex.com')).toBeVisible();
  });

  test('should search users', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Buscar por email...');
    await searchInput.fill('user1');
    await page.waitForTimeout(1000);
    await expect(page.getByText('user1@ex.com')).toBeVisible();
    await expect(page.getByText('user2@ex.com')).not.toBeVisible();
  });

  test('should view user details', async ({ page }) => {
    await page.getByTitle('Ver detalhes').first().click();
    await expect(page.getByRole('heading', { name: 'Estatísticas' })).toBeVisible();
    await page.getByRole('button', { name: 'Fechar' }).click();
  });

  test('should delete user', async ({ page }) => {
    await page.getByTitle('Deletar user1@ex.com').click();
    await expect(page.getByTestId('confirmation-modal')).toBeVisible();
    await page.getByTestId('confirm-accept').click();
    await expect(page.getByText('Usuário deletado com sucesso').first()).toBeVisible();
  });
});
