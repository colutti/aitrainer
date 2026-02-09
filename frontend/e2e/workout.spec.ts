import { test, expect } from '@playwright/test';

test.describe('Workouts Feature', () => {
  test.beforeEach(async ({ context, page }) => {
    // PROTECT BACKEND
    await page.route(url => url.pathname.startsWith('/api/'), async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ detail: `Unmocked API call: ${route.request().url()}` }) });
    });

    // Mock user profile
    await page.route('**/api/user/me', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ name: 'User', email: 'user@ex.com' }) });
    });

    // Set auth token before navigation
    await context.addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
    });
    
    await page.goto('/workouts');
  });

  test('should display workouts list and search', async ({ page }) => {
    const mockWorkouts = [
        { 
          id: 'w1', 
          date: '2026-02-08', 
          workout_type: 'Peito e Tríceps', 
          exercises: [{ name: 'Supino', reps_per_set: [10], weights_per_set: [80] }] 
        },
        { 
          id: 'w2', 
          date: '2026-02-07', 
          workout_type: 'Costa e Bíceps', 
          exercises: [{ name: 'Remada', reps_per_set: [12], weights_per_set: [60] }] 
        }
    ];

    await page.route('**/api/workout/list*', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ workouts: mockWorkouts, total: 2, total_pages: 1, page: 1 }) });
    });

    await page.reload();
    await expect(page.getByText('Peito e Tríceps')).toBeVisible();
    await expect(page.getByText('Costa e Bíceps')).toBeVisible();

    // Search
    await page.getByPlaceholder('Buscar por tipo ou exercício...').fill('Peito');
    await expect(page.getByText('Costa e Bíceps')).not.toBeVisible();
  });

  test('should open workout details and delete', async ({ page }) => {
    const mockWorkout = { 
        id: 'w1', 
        date: '2026-02-08', 
        workout_type: 'Peito', 
        exercises: [{ 
            name: 'Supino', 
            reps_per_set: [10],
            weights_per_set: [80]
        }],
        notes: 'Good session'
    };

    await page.route('**/api/workout/list*', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ workouts: [mockWorkout], total: 1, total_pages: 1, page: 1 }) });
    });

    await page.reload();

    // Open detail
    await page.getByText('Peito').click();
    await expect(page.getByText('Detalhes do Treino')).toBeVisible();
    await expect(page.getByText('Supino')).toBeVisible();
    await expect(page.getByText('80kg')).toBeVisible();
    await expect(page.getByText('Good session')).toBeVisible();

    // Close
    await page.getByRole('button', { name: 'Close' }).or(page.locator('button:has(svg.lucide-x)')).click();

    // Delete
    await page.route('**/api/workout/w1', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    await page.getByTitle('Excluir treino').click();
    
    // Confirmation modal
    await expect(page.getByText('Tem certeza que deseja excluir')).toBeVisible();
    await page.getByRole('button', { name: 'Excluir', exact: true }).click();

    await expect(page.getByText('Treino excluído com sucesso!').first()).toBeVisible();
  });
});
