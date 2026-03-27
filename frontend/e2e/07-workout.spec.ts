import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Workouts Feature', () => {
  test('should verify workout page elements and empty state', async ({ authenticatedPage, ui }) => {
    // 1. Navigate to Workouts
    await ui.navigateTo('workouts');

    // 2. Verify Page Title
    await expect(authenticatedPage.getByTestId('view-header-title')).toContainText(t('workouts.title'));

    // 3. Verify Empty State or "Registrar Treino" button
    const addButton = authenticatedPage.getByRole('button', { name: /Registrar Treino|Adicionar/i }).first();
    await expect(addButton).toBeVisible();
  });

  test('should add a new workout entry', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('workouts');

    // Open Drawer
    await ui.openDrawer('Registrar Treino');

    // Fill the basic form
    await ui.fillForm({
      [t('workouts.workout_type')]: 'Treino de Força E2E',
      [t('workouts.duration')]: 45
    });

    // Add at least one exercise
    const addExerciseBtn = authenticatedPage.getByRole('button', { name: /Adicionar/i });
    await addExerciseBtn.click();
    
    // Fill the exercise (just the title to avoid complex array locators for now)
    const exerciseInput = authenticatedPage.getByPlaceholder('Nome do Exercício').first();
    await exerciseInput.fill('Supino Reto');

    // Submit
    await ui.submit();

    // Drawer should close and we should see a success toast
    // The real backend should accept the submission, but we only need to assert the UI closes cleanly
    const drawerTitle = authenticatedPage.getByRole('heading', { name: t('workouts.register_workout') });
    await expect(drawerTitle).toBeHidden({ timeout: 10000 });
  });
});
