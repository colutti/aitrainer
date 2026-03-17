import { test, expect } from '@playwright/test';

test.describe('Workouts Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Reset storage state
    await page.context().addInitScript(() => {
      window.localStorage.setItem('auth_token', 'mock-jwt');
      window.localStorage.setItem('i18nextLng', 'pt-BR');
      window.localStorage.setItem('has_seen_tour_dashboard-main-user@ex.com', 'true');
    });

    // Mock user profile
    await page.route(/\/api\/user\/me/, async (route) => {
      await route.fulfill({ 
        status: 200, 
        body: JSON.stringify({ name: 'User', email: 'user@ex.com', role: 'user', onboarding_completed: true }) 
      });
    });

    // FALLBACK for /api/
    await page.route(url => url.pathname.startsWith('/api/') && !url.pathname.includes('/workout'), async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({}) });
    });
  });

  test('should display workouts list and search', async ({ page }) => {
    const mockWorkouts = [
        { 
          id: 'w1', 
          user_email: 'user@ex.com',
          date: '2026-02-08', 
          workout_type: 'Peito e Tríceps', 
          exercises: [{ name: 'Supino', sets: [{ reps: 10, weight_kg: 80 }] }],
          duration_minutes: 60,
          source: 'manual'
        }
    ];

    await page.route('**/api/workout/list*', async (route) => {
        await route.fulfill({ status: 200, body: JSON.stringify({ workouts: mockWorkouts, total: 1, total_pages: 1, page: 1 }) });
    });

    await page.goto('/dashboard/workouts');
    await page.waitForLoadState('networkidle');
    
    await expect(page.getByText(/Peito e Tríceps/i)).toBeVisible();

    // Search
    await page.getByPlaceholder(/Buscar por tipo ou exercício/i).fill('Peito');
    await expect(page.getByText(/Peito e Tríceps/i)).toBeVisible();
  });
});
