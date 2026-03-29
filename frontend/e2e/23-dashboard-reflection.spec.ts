import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Dashboard reflection', () => {
  test('reflects workout, weight, and nutrition data created in the same test', async ({ authenticatedPage, ui, api }) => {
    test.setTimeout(120000);
    const workoutType = `Dashboard Signal ${Date.now()}`;
    const workoutExercise = 'Supino Reto';
    const weightValue = 81.7;
    const fatValue = 18.9;
    const calories = 1020;
    const protein = 68;
    const carbs = 90;
    const fat = 28;
    const date = new Date().toISOString().split('T')[0];

    await ui.navigateTo('workouts');
    await ui.openDrawer(t('workouts.register_workout'));
    await ui.fillForm({
      [t('workouts.workout_type')]: workoutType,
      [t('workouts.duration')]: 55,
    });
    await authenticatedPage.getByRole('button', { name: /Adicionar/i }).first().click();
    await authenticatedPage.getByPlaceholder('Nome do Exercício').first().fill(workoutExercise);
    await ui.submit();
    await expect(authenticatedPage.getByTestId('workout-card').filter({ hasText: workoutType }).first()).toBeVisible({ timeout: 15000 });

    await ui.navigateTo('body');
    await ui.openDrawer(t('body.weight.register_weight'));
    await ui.fillForm({
      [t('body.weight.weight')]: weightValue,
      [t('body.weight.body_fat')]: fatValue,
    });
    await authenticatedPage.getByLabel(t('body.weight.notes')).fill(`dashboard-reflection-${Date.now()}`);
    await ui.submit();
    await expect(authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(weightValue) }).first()).toBeVisible({ timeout: 15000 });

    const nutritionResponse = await api.post('/nutrition/log', {
      data: {
        date,
        source: 'Manual E2E',
        calories,
        protein_grams: protein,
        carbs_grams: carbs,
        fat_grams: fat,
      },
    });
    expect(nutritionResponse.status()).toBe(200);

    await ui.navigateTo('dashboard');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText('81.7kg');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText(String(calories));
    await expect(authenticatedPage.getByText(new RegExp(workoutType, 'i'))).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Refeição Registrada/i)).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText('81.7kg');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toContainText(String(calories));
    await expect(authenticatedPage.getByText(new RegExp(workoutType, 'i'))).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toContainText(/\d{4}/);
  });
});
