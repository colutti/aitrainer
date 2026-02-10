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

  test('should show empty state when no workouts', async ({ page }) => {
    await page.route('**/api/workout/list*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ workouts: [], total: 0, total_pages: 1, page: 1 }) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Nenhum treino encontrado')).toBeVisible();
  });

  test('should cancel delete confirmation', async ({ page }) => {
    const mockWorkout = { id: 'w1', date: '2026-02-08', workout_type: 'Peito', exercises: [] };

    await page.route('**/api/workout/list*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ workouts: [mockWorkout], total: 1, total_pages: 1, page: 1 }) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Wait for workout to be visible before trying to click delete
    await expect(page.getByText('Peito')).toBeVisible();

    // Click delete button
    await page.locator('button[title="Excluir treino"]').click({ force: true });

    // Confirmation modal should appear
    await expect(page.getByTestId('confirmation-modal')).toBeVisible();

    // Cancel
    await page.getByTestId('confirm-cancel').click();

    // Modal should close and workout should still be visible
    await expect(page.getByTestId('confirmation-modal')).not.toBeVisible();
    await expect(page.getByText('Peito')).toBeVisible();
  });

  test('should handle delete API error', async ({ page }) => {
    const mockWorkout = { id: 'w1', date: '2026-02-08', workout_type: 'Peito', exercises: [] };

    await page.route('**/api/workout/list*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ workouts: [mockWorkout], total: 1, total_pages: 1, page: 1 }) });
    });

    await page.route('**/api/workout/w1', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) });
      }
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    await page.getByTitle('Excluir treino').click({ force: true });
    await page.getByTestId('confirm-accept').click();

    await expect(page.getByText('Erro ao excluir treino.').first()).toBeVisible();
  });

  test('should display workout exercises in drawer', async ({ page }) => {
    const mockWorkout = {
      id: 'w1',
      date: '2026-02-08',
      workout_type: 'Peito',
      exercises: [
        { name: 'Supino', reps_per_set: [10, 10], weights_per_set: [80, 80] },
        { name: 'Agachamento', reps_per_set: [12], weights_per_set: [100] }
      ],
      notes: 'Treino intenso'
    };

    await page.route('**/api/workout/list*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ workouts: [mockWorkout], total: 1, total_pages: 1, page: 1 }) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Open drawer
    await page.getByText('Peito').click();

    await expect(page.getByText('Detalhes do Treino')).toBeVisible();
    await expect(page.getByText('Supino')).toBeVisible();
    await expect(page.getByText('Agachamento')).toBeVisible();
    await expect(page.getByText('80kg').first()).toBeVisible();
    await expect(page.getByText('Treino intenso')).toBeVisible();
  });

  test('should filter workouts by exercise name', async ({ page }) => {
    const mockWorkouts = [
      { id: 'w1', date: '2026-02-08', workout_type: 'Peito', exercises: [{ name: 'Supino', reps_per_set: [10], weights_per_set: [80] }] },
      { id: 'w2', date: '2026-02-07', workout_type: 'Pernas', exercises: [{ name: 'Agachamento', reps_per_set: [12], weights_per_set: [100] }] }
    ];

    await page.route('**/api/workout/list*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify({ workouts: mockWorkouts, total: 2, total_pages: 1, page: 1 }) });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    await expect(page.getByText('Peito')).toBeVisible();
    await expect(page.getByText('Pernas')).toBeVisible();

    // Filter by exercise name
    await page.getByPlaceholder('Buscar por tipo ou exercício...').fill('Agachamento');

    // Only Pernas workout should be visible (has Agachamento exercise)
    await expect(page.getByText('Pernas')).toBeVisible();
    await expect(page.getByText('Peito')).not.toBeVisible();
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
