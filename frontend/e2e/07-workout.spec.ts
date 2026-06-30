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
    const workoutDate = '2026-04-14';
    const createdPrimaryExercise = 'Supino Reto';
    const createdSecondaryExercise = 'Row Erg';

    await workoutsPage.locator('#workout-date').fill(workoutDate);
    await workoutsPage.locator('#workout-type').fill(workoutType);
    await workoutsPage.locator('#workout-duration').fill('62');

    await workoutsPage.getByRole('button', { name: t('workouts.add_exercise') }).click();
    await workoutsPage.locator('#exercise-0').fill(createdPrimaryExercise);
    await workoutsPage.locator('#exercise-0-set-0-weight').fill('60');
    await workoutsPage.locator('#exercise-0-set-0-reps').fill('10');
    await workoutsPage.getByRole('button', { name: t('workouts.duplicate_set') }).click();
    await workoutsPage.locator('#exercise-0-set-1-weight').fill('70');
    await workoutsPage.locator('#exercise-0-set-1-reps').fill('8');

    await workoutsPage.getByRole('button', { name: t('workouts.add_exercise') }).click();
    await workoutsPage.locator('#exercise-1').fill(createdSecondaryExercise);
    await workoutsPage.locator('#exercise-1-set-0-weight').fill('0');
    await workoutsPage.locator('#exercise-1-set-0-reps').fill('1');
    await workoutsPage.locator('#exercise-1-set-0-duration').fill('110');
    await workoutsPage.locator('#exercise-1-set-0-distance').fill('500');
    await workoutsPage
      .getByRole('button', { name: t('workouts.add_set') })
      .nth(1)
      .click();
    await workoutsPage.locator('#exercise-1-set-1-weight').fill('0');
    await workoutsPage.locator('#exercise-1-set-1-reps').fill('1');
    await workoutsPage.locator('#exercise-1-set-1-duration').fill('115');
    await workoutsPage.locator('#exercise-1-set-1-distance').fill('500');

    await ui.submit();
    const createdCard = workoutsPage.getByTestId('workout-card').filter({ hasText: workoutType }).first();
    await expect(createdCard).toBeVisible({ timeout: 15000 });
    await expect(createdCard).toContainText('2');
    await expect(createdCard).toContainText('1.2t');

    await createdCard.click();
    await expect(workoutsPage.getByRole('heading', { name: t('workouts.edit_workout') })).toBeVisible({ timeout: 15000 });
    await expect(workoutsPage.locator('#workout-date')).toHaveValue(workoutDate);
    await expect(workoutsPage.locator('#workout-type')).toHaveValue(workoutType);
    await expect(workoutsPage.locator('#workout-duration')).toHaveValue('62');
    await expect(workoutsPage.locator('#exercise-0')).toHaveValue(createdPrimaryExercise);
    await expect(workoutsPage.locator('#exercise-0-set-0-weight')).toHaveValue('60');
    await expect(workoutsPage.locator('#exercise-0-set-1-reps')).toHaveValue('8');
    await expect(workoutsPage.locator('#exercise-1')).toHaveValue(createdSecondaryExercise);
    await expect(workoutsPage.locator('#exercise-1-set-0-duration')).toHaveValue('110');
    await expect(workoutsPage.locator('#exercise-1-set-1-distance')).toHaveValue('500');
    await workoutsPage.keyboard.press('Escape');

    await createdCard.getByLabel(/Editar|Edit|Editar/i).click();
    const updatedWorkoutType = `${workoutType} Updated`;
    const updatedWorkoutDate = '2026-04-15';
    const updatedPrimaryExercise = 'Supino Inclinado';
    const updatedSecondaryExercise = 'Bike Erg';
    await workoutsPage.locator('#workout-date').fill(updatedWorkoutDate);
    await workoutsPage.locator('#workout-type').fill(updatedWorkoutType);
    await workoutsPage.locator('#workout-duration').fill('54');
    await workoutsPage.locator('#exercise-0').fill(updatedPrimaryExercise);
    await workoutsPage.locator('#exercise-0-set-0-weight').fill('65');
    await workoutsPage.locator('#exercise-0-set-0-reps').fill('10');
    await workoutsPage.locator('#exercise-0-set-1-weight').fill('75');
    await workoutsPage.locator('#exercise-0-set-1-reps').fill('6');
    await workoutsPage.locator('#exercise-1').fill(updatedSecondaryExercise);
    await workoutsPage.locator('#exercise-1-set-0-duration').fill('120');
    await workoutsPage.locator('#exercise-1-set-0-distance').fill('650');
    await workoutsPage.locator('#exercise-1-set-1-duration').fill('125');
    await workoutsPage.locator('#exercise-1-set-1-distance').fill('700');
    await ui.submit();
    const updatedCard = workoutsPage.getByTestId('workout-card').filter({ hasText: updatedWorkoutType }).first();
    await expect(updatedCard).toBeVisible({ timeout: 15000 });
    await expect(updatedCard).toContainText('1.1t');

    await workoutsPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('workouts');
    await expect(updatedCard).toBeVisible({ timeout: 15000 });
    await updatedCard.click();
    await expect(workoutsPage.getByRole('heading', { name: t('workouts.edit_workout') })).toBeVisible({ timeout: 15000 });
    await expect(workoutsPage.locator('#workout-date')).toHaveValue(updatedWorkoutDate);
    await expect(workoutsPage.locator('#workout-duration')).toHaveValue('54');
    await expect(workoutsPage.locator('#exercise-0')).toHaveValue(updatedPrimaryExercise);
    await expect(workoutsPage.locator('#exercise-0-set-0-weight')).toHaveValue('65');
    await expect(workoutsPage.locator('#exercise-1')).toHaveValue(updatedSecondaryExercise);
    await expect(workoutsPage.locator('#exercise-1-set-1-distance')).toHaveValue('700');
    await workoutsPage.keyboard.press('Escape');

    await updatedCard.getByLabel(/Excluir|Delete|Eliminar/i).click();
    const confirmDeleteButton = workoutsPage.getByTestId('confirm-accept');
    await expect(confirmDeleteButton).toBeVisible({ timeout: 15000 });
    await confirmDeleteButton.click();
    await expect(updatedCard).not.toBeVisible({ timeout: 15000 });

    await workoutsPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('workouts');
    await expect(workoutsPage.getByTestId('workout-card').filter({ hasText: updatedWorkoutType })).toHaveCount(0);
  });
});
