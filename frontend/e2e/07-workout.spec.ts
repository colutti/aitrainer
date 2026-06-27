import { test, expect } from './fixtures';
import { bootstrapOnboardedUser } from './helpers/bootstrap';
import { t } from './helpers/translations';

test.describe('Workouts Feature', () => {
  test('should create, update, reload and delete a manual workout', async ({ page, ui }, testInfo) => {
    const workoutsPage = await bootstrapOnboardedUser(page, testInfo);

    await ui.navigateTo('workouts');
    await expect(workoutsPage.getByRole('button', { name: t('workouts.register_workout') })).toBeVisible({ timeout: 15000 });
    await ui.openDrawer(t('workouts.register_workout'));

    const workoutType = `E2E Workout ${Date.now()}`;
    await ui.fillForm({
      [t('workouts.workout_type')]: workoutType,
      [t('workouts.duration')]: 45,
    });

    const addExerciseBtn = workoutsPage.getByRole('button', { name: /Adicionar/i });
    await addExerciseBtn.click();
    await workoutsPage.getByLabel(t('workouts.exercise_name')).fill('Supino Reto');

    await ui.submit();
    const createdCard = workoutsPage.getByTestId('workout-card').filter({ hasText: workoutType }).first();
    await expect(createdCard).toBeVisible({ timeout: 15000 });

    await createdCard.click();
    const updatedWorkoutType = `${workoutType} Updated`;
    await workoutsPage.getByLabel(t('workouts.workout_type')).fill(updatedWorkoutType);
    await ui.submit();
    const updatedCard = workoutsPage.getByTestId('workout-card').filter({ hasText: updatedWorkoutType }).first();
    await expect(updatedCard).toBeVisible({ timeout: 15000 });

    await workoutsPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('workouts');
    await expect(updatedCard).toBeVisible({ timeout: 15000 });

    await updatedCard.getByLabel(/Excluir|Delete/i).click();
    const confirmDeleteButton = workoutsPage.getByTestId('confirm-accept');
    await expect(confirmDeleteButton).toBeVisible({ timeout: 15000 });
    await confirmDeleteButton.click();
    await expect(updatedCard).not.toBeVisible({ timeout: 15000 });

    await workoutsPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('workouts');
    await expect(workoutsPage.getByTestId('workout-card').filter({ hasText: updatedWorkoutType })).toHaveCount(0);
  });
});
