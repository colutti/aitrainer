import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Workout Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should list workouts and show details', async ({ authenticatedPage, api }) => {
    // Seed a workout
    await api.post('/workout', {
      workout_type: 'Força',
      duration_minutes: 60,
      exercises: [{ name: 'Supino', sets: 1, reps_per_set: [10], weights_per_set: [60] }]
    });

    await authenticatedPage.goto('/dashboard/workouts');
    await authenticatedPage.waitForLoadState('networkidle');

    // 1. Verify in list
    const card = authenticatedPage.locator('.bg-dark-card').filter({ hasText: /Força/i }).first();
    await expect(card).toBeVisible({ timeout: 15000 });

    // 2. Click to see details (Card)
    await card.click();
    
    // 3. Check drawer details
    await expect(authenticatedPage.getByText(/Detalhes do Treino/i).first()).toBeVisible();
    await expect(authenticatedPage.getByText(/Supino/i).first()).toBeVisible();
  });

  test('should delete a workout', async ({ authenticatedPage, api }) => {
    // 1. Setup: add a workout first
    await api.post('/workout', {
      workout_type: 'Leg Day',
      duration_minutes: 45,
      exercises: []
    });

    await authenticatedPage.goto('/dashboard/workouts');
    await authenticatedPage.waitForLoadState('networkidle');

    // 2. Click delete button
    const card = authenticatedPage.locator('.bg-dark-card').filter({ hasText: /Leg Day/i }).first();
    await expect(card).toBeVisible({ timeout: 10000 });
    
    await card.hover();
    const deleteBtn = card.locator('button').filter({ has: authenticatedPage.locator('svg') }).first();
    await deleteBtn.click({ force: true });

    // 3. Confirm in modal
    const confirmBtn = authenticatedPage.locator('button').filter({ hasText: /Confirmar|Sim|Excluir/i }).last();
    await confirmBtn.click({ force: true });

    // 4. Verify gone
    await expect(authenticatedPage.getByText(/Leg Day/i)).not.toBeVisible({ timeout: 15000 });
  });
});
