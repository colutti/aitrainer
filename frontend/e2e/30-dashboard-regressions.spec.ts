import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Dashboard Regressions', () => {
  test('keeps workout activity reachable after a hard reload and page scroll', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('workouts');
    await ui.openDrawer('Registrar Treino');

    const workoutType = `Dashboard Regression ${Date.now()}`;
    await ui.fillForm({
      [t('workouts.workout_type')]: workoutType,
      [t('workouts.duration')]: 35,
    });

    await authenticatedPage.getByRole('button', { name: /Adicionar/i }).click();
    await authenticatedPage.getByPlaceholder('Nome do Exercício').first().fill('Agachamento Livre');
    await ui.submit();

    await expect(authenticatedPage.getByTestId('workout-card').filter({ hasText: workoutType }).first()).toBeVisible({ timeout: 15000 });

    await ui.navigateTo('dashboard');
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });

    const footerNote = authenticatedPage.getByText(t('body.metabolism.info_desc'));
    await footerNote.scrollIntoViewIfNeeded();
    await expect(footerNote).toBeVisible({ timeout: 15000 });

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await expect(authenticatedPage.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByTestId('widget-metabolism')).toBeVisible({ timeout: 15000 });
    await footerNote.scrollIntoViewIfNeeded();
    await expect(footerNote).toBeVisible({ timeout: 15000 });
  });
});
