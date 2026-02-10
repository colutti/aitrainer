import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill login form
    await page.getByLabel('Endereço de Email').fill('test@example.com');
    await page.getByLabel('Senha').fill('testpassword123');
    
    // Mock API response
    await page.route('**/api/user/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'mock-jwt-token' }),
      });
    });

    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ 
          email: 'test@example.com', 
          role: 'user',
          name: 'Test User'
        }),
      });
    });

    // Submit form
    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();

    // Should redirect to dashboard (root path)
    await expect(page).toHaveURL('/');
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.getByLabel('Endereço de Email').fill('wrong@example.com');
    await page.getByLabel('Senha').fill('wrongpassword');

    // Mock API error response
    await page.route('**/api/user/login', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid credentials' }),
      });
    });

    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();

    // Should show error message from notify.error
    await expect(page.getByTestId('toast').first()).toBeVisible();
  });

  test('should show error toast on server error (500)', async ({ page }) => {
    await page.goto('/login');

    await page.route('**/api/user/login', async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) });
    });

    await page.getByLabel('Endereço de Email').fill('test@example.com');
    await page.getByLabel('Senha').fill('password123');
    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();

    // Should show error toast
    await expect(page.getByTestId('toast').first()).toBeVisible();
  });

  test('should not submit with empty email', async ({ page }) => {
    await page.goto('/login');

    // Only fill password, leave email empty
    await page.getByLabel('Senha').fill('password123');
    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();

    // Should show email validation error
    await expect(page.getByText(/Email inválido/i).or(page.getByText(/obrigatório/i))).toBeVisible();
  });

  test('should display password as type password', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.getByLabel('Senha');
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('should validate required fields and formats', async ({ page }) => {
    await page.goto('/login');

    // 1. Empty fields
    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();
    await expect(page.getByText(/Email inválido/i).or(page.getByText(/obrigatório/i))).toBeVisible();

    // 2. Invalid email format
    await page.getByLabel('Endereço de Email').fill('not-an-email');
    await page.getByLabel('Senha').fill('123456');
    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();
    await expect(page.getByText(/Email inválido/i)).toBeVisible();

    // 3. Short password
    await page.getByLabel('Endereço de Email').fill('test@example.com');
    await page.getByLabel('Senha').fill('123');
    await page.getByRole('button', { name: /Entrar na Plataforma/i }).click();
    await expect(page.getByText(/pelo menos 6 caracteres/i)).toBeVisible();
  });
});
