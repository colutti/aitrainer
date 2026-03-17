import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Workout Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test.skip('should create and list workouts', async ({ authenticatedPage }) => {
    // Manual creation is currently disabled in the UI (button is hidden and drawer has no form)
    /*
    await authenticatedPage.goto('/dashboard/workouts');
    ...
    */
  });

  test('should delete a workout', async ({ authenticatedPage, api }) => {
    // 1. Seed a workout via API
    await api.post('/workout', {
      workout_type: 'Treino para deletar',
      exercises: [
        { 
          name: 'Supino', 
          sets: 3, 
          reps_per_set: [10, 10, 10], 
          weights_per_set: [60, 60, 60] 
        }
      ],
      date: new Date().toISOString(),
      source: 'manual'
    });

    await authenticatedPage.goto('/dashboard/workouts');
    await expect(authenticatedPage.getByText('Treino para deletar')).toBeVisible();

    // 2. Click delete button on the card
    // Cards usually have a trash icon or a "Excluir" button
    await authenticatedPage.locator('button:has-text("Excluir")').or(authenticatedPage.locator('.lucide-trash-2')).first().click();

    // 3. Confirm deletion in modal
    await authenticatedPage.locator('button:has-text("Confirmar")').or(authenticatedPage.locator('button:has-text("Excluir")')).last().click();

    // Verify it's gone
    await expect(authenticatedPage.getByText('Treino para deletar')).not.toBeVisible();
    await expect(authenticatedPage.getByText(/Nenhum treino registrado/i)).toBeVisible();
  });
});
