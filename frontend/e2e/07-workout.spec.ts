import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Workouts Feature', () => {
  test('should create a workout and keep it after reload', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('workouts');
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('workouts.title'));
    await ui.openDrawer('Registrar Treino');

    const workoutType = `E2E Workout ${Date.now()}`;
    await ui.fillForm({
      [t('workouts.workout_type')]: workoutType,
      [t('workouts.duration')]: 45,
    });

    const addExerciseBtn = authenticatedPage.getByRole('button', { name: /Adicionar/i });
    await addExerciseBtn.click();
    await authenticatedPage.getByPlaceholder('Nome do Exercício').first().fill('Supino Reto');

    await ui.submit();
    await expect(authenticatedPage.getByText(new RegExp(workoutType, 'i'))).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('workouts');
    const workoutCard = authenticatedPage.getByTestId('workout-card').filter({ hasText: workoutType }).first();
    await expect(workoutCard).toBeVisible({ timeout: 15000 });

    await workoutCard.click();
    await expect(authenticatedPage.getByRole('heading', { name: t('workouts.edit_workout') })).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByLabel(t('workouts.workout_type'))).toHaveValue(workoutType);
    await expect(authenticatedPage.getByPlaceholder('Nome do Exercício').first()).toHaveValue('Supino Reto');
  });
});
