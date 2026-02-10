import { test, expect } from '@playwright/test';

const mockUsers = [
  { email: 'user1@ex.com', name: 'User One', is_admin: false, created_at: '2026-01-01T00:00:00Z' },
  { email: 'user2@ex.com', name: 'User Two', is_admin: false, created_at: '2026-01-15T00:00:00Z' },
  { email: 'admin@ex.com', name: 'Admin User', is_admin: true, created_at: '2025-12-01T00:00:00Z' },
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
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Mock admin user
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ name: 'Admin', email: 'admin@ex.com', role: 'admin' }) });
    });

    // Mock users list - URL format is /api/admin/users/?page=1&page_size=20
    await page.route(/\/api\/admin\/users\//, async (route) => {
      if (route.request().method() === 'GET' && !route.request().url().match(/\/users\/[^?/]+$/)) {
        await route.fulfill({ status: 200, body: JSON.stringify(mockUsersResponse) });
      }
    });

    // Set auth token before navigation
    await context.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
    });

    await page.goto('/admin/users');
    await page.waitForLoadState('networkidle');
    // Wait for debounced initial load (500ms delay)
    await page.waitForTimeout(700);
    await page.waitForLoadState('networkidle');
  });

  test('should display users list with ADMIN/USER badges', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Gestão de Usuários' })).toBeVisible();
    await expect(page.getByText('user1@ex.com')).toBeVisible();
    await expect(page.getByText('admin@ex.com')).toBeVisible();
    await expect(page.getByText('ADMIN').first()).toBeVisible();
    await expect(page.getByText('USER').first()).toBeVisible();
  });

  test('should search users by email', async ({ page }) => {
    // Mock filtered response - matches /api/admin/users/?page=1&page_size=20&search=user1
    await page.route(/\/api\/admin\/users\//, async (route) => {
      const url = route.request().url();
      if (url.includes('search=user1')) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            users: [mockUsers[0]],
            total: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
          }),
        });
      } else {
        await route.fulfill({ status: 200, body: JSON.stringify(mockUsersResponse) });
      }
    });

    const searchInput = page.getByPlaceholder('Buscar por email...');
    await searchInput.fill('user1');

    // Wait for debounced search (500ms)
    await page.waitForTimeout(700);
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('user1@ex.com')).toBeVisible();
    await expect(page.getByText('user2@ex.com')).not.toBeVisible();
  });

  test('should view user details modal', async ({ page }) => {
    const userDetail = { ...mockUsers[0], last_login: '2026-02-10T08:00:00Z' };

    await page.route(/\/api\/admin\/users\/user1/, async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(userDetail) });
    });

    await page.getByTitle('Ver detalhes').first().click();

    await expect(page.getByRole('heading', { name: 'Detalhes do Usuário' })).toBeVisible();
    await expect(page.getByText('user1@ex.com').first()).toBeVisible();

    // Close modal
    await page.getByRole('button', { name: 'Fechar' }).click();
    await expect(page.getByRole('heading', { name: 'Detalhes do Usuário' })).not.toBeVisible();
  });

  test('should delete non-admin user with confirmation', async ({ page }) => {
    await page.route(/\/api\/admin\/users\/user1/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
      }
    });

    await page.getByTitle('Deletar user1@ex.com').click();

    // Check confirmation modal
    await expect(page.getByTestId('confirmation-modal')).toBeVisible();
    await expect(page.getByText(/Deseja realmente deletar o usuário user1@ex.com/)).toBeVisible();

    // Confirm deletion
    await page.getByTestId('confirm-accept').click();

    await expect(page.getByText('Usuário deletado com sucesso').first()).toBeVisible();
  });

  test('should not show delete button for admin users', async ({ page }) => {
    // Verify that the admin user has no delete button
    const adminDeleteBtn = page.getByTitle('Deletar admin@ex.com');
    await expect(adminDeleteBtn).not.toBeVisible();
  });

  test('should cancel delete confirmation', async ({ page }) => {
    await page.getByTitle('Deletar user1@ex.com').click();

    await expect(page.getByTestId('confirmation-modal')).toBeVisible();

    // Cancel deletion
    await page.getByTestId('confirm-cancel').click();

    await expect(page.getByTestId('confirmation-modal')).not.toBeVisible();
    // User should still be visible
    await expect(page.getByText('user1@ex.com')).toBeVisible();
  });

  test('should handle delete API error', async ({ page }) => {
    await page.route(/\/api\/admin\/users\/user1/, async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) });
      }
    });

    await page.getByTitle('Deletar user1@ex.com').click();
    await page.getByTestId('confirm-accept').click();

    await expect(page.getByText('Erro ao deletar usuário').first()).toBeVisible();
  });

  test('should handle pagination', async ({ page }) => {
    // Mock response with multiple pages
    await page.route(/\/api\/admin\/users\//, async (route) => {
      if (route.request().method() === 'GET') {
        const url = route.request().url();
        const pageMatch = url.match(/page=(\d+)/);
        const currentPage = pageMatch ? parseInt(pageMatch[1]) : 1;

        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            users: currentPage === 1
              ? [mockUsers[0], mockUsers[1]]
              : [mockUsers[2]],
            total: 3,
            page: currentPage,
            page_size: 20,
            total_pages: 2,
          }),
        });
      }
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(700);

    await expect(page.getByText('Página 1 de 2')).toBeVisible();

    // Click next page button (icon-only button, use nth to get the "next" one after the page indicator)
    const paginationButtons = page.locator('button[variant="ghost"], button').filter({ has: page.locator('svg') });
    // The "next" button is the second pagination button (first is "previous")
    await page.locator('div.flex.justify-center button').last().click();

    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Página 2 de 2')).toBeVisible();
    await expect(page.getByText('admin@ex.com')).toBeVisible();
  });

  test('should show empty state when no users found', async ({ page }) => {
    await page.route(/\/api\/admin\/users\//, async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          users: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        }),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(700);

    await expect(page.getByText('Nenhum usuário encontrado.')).toBeVisible();
  });

  test('should handle users list API error', async ({ page }) => {
    await page.route(/\/api\/admin\/users\//, async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(700);

    await expect(page.getByText('Erro ao carregar usuários.').first()).toBeVisible();
  });
});
