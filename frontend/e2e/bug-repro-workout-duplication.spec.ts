import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Workouts Duplication Bug Reproduction', () => {
  test('should not duplicate a workout when editing it', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('workouts');
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('workouts.title'));
    
    // 1. Create a workout
    await ui.openDrawer(t('workouts.register_workout'));

    const workoutType = `REPRO-BUG-${Date.now()}`;
    await ui.fillForm({
      [t('workouts.workout_type')]: workoutType,
      [t('workouts.duration')]: 30,
    });

    const addExerciseBtn = authenticatedPage.getByRole('button', { name: t('workouts.add_exercise') });
    await addExerciseBtn.click();
    await authenticatedPage.getByPlaceholder(t('workouts.exercise_name')).first().fill('Test Exercise');

    await ui.submit();
    await expect(authenticatedPage.getByText(new RegExp(workoutType, 'i'))).toBeVisible({ timeout: 15000 });

    // 2. Edit the workout
    const workoutCard = authenticatedPage.getByTestId('workout-card').filter({ hasText: workoutType }).first();
    await workoutCard.click();
    
    await expect(authenticatedPage.getByRole('heading', { name: t('workouts.edit_workout') })).toBeVisible({ timeout: 15000 });
    
    // Change the workout type slightly
    const updatedWorkoutType = `${workoutType}-UPDATED`;
    await authenticatedPage.getByLabel(t('workouts.workout_type')).clear();
    await authenticatedPage.getByLabel(t('workouts.workout_type')).fill(updatedWorkoutType);
    
    await ui.submit();
    
    // 3. Check for duplication
    // We expect ONLY the updated workout type to be visible.
    // If it's duplicating, we might see both, or at least 2 cards.
    await expect(authenticatedPage.getByText(new RegExp(updatedWorkoutType, 'i'))).toBeVisible({ timeout: 15000 });
    
    // Wait a bit for any potential duplicates to appear
    await authenticatedPage.waitForTimeout(2000);
    
    const workoutCards = authenticatedPage.getByTestId('workout-card');
    const count = await workoutCards.count();
    
    // Since we just created 1 and edited it, we should have exactly 1.
    // If it's duplicating, we'll have 2 (one old, one new).
    // Note: This assumes a fresh test user/state, which the E2E fixtures usually provide.
    expect(count).toBe(1);
  });
});
