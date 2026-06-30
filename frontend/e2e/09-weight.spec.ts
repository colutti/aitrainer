import { test, expect } from './fixtures';
import { bootstrapOnboardedUser } from './helpers/bootstrap';
import { t } from './helpers/translations';

test.describe('Weight Tracking Feature', () => {
  test('should create, edit, reload and delete a weight log through the UI', async ({ page, ui }, testInfo) => {
    const authenticatedPage = await bootstrapOnboardedUser(page, testInfo);
    await ui.navigateTo('body');
    await expect(authenticatedPage.getByTestId('body-insight-screen')).toBeVisible({ timeout: 15000 });
    await ui.openDrawer(t('body.weight.register_weight'));
    await authenticatedPage.getByText(t('body.weight.composition_toggle'), { exact: false }).click();
    await authenticatedPage.getByText(t('body.weight.measurements_toggle'), { exact: false }).click();

    const newDate = '2026-04-18';
    const newWeight = 78.5;
    const newFat = 18.2;
    const newMuscleKg = 34.1;
    const newVisceralFat = 8;
    const newBodyWater = 57.8;
    const newBoneMass = 3.4;
    const newBmr = 1765;
    const newNeck = 39;
    const newChest = 103;
    const newWaist = 84;
    const newHips = 98;
    const newBicepR = 36;
    const newBicepL = 35.5;
    const newThighR = 57;
    const newThighL = 56.5;
    const newCalfR = 37.5;
    const newCalfL = 37;
    const notes = `E2E weight note ${Date.now()}`;

    await authenticatedPage.locator('#weight-date').fill(newDate);
    await ui.fillForm({
      [t('body.weight.weight')]: newWeight,
      [t('body.weight.body_fat')]: newFat,
    });
    await authenticatedPage.getByLabel(`${t('body.weight.muscle_mass')} (kg)`).fill(String(newMuscleKg));
    await authenticatedPage.getByLabel(t('body.weight.visceral_fat')).fill(String(newVisceralFat));
    await authenticatedPage.getByLabel(t('body.weight.body_water')).fill(String(newBodyWater));
    await authenticatedPage.getByLabel(t('body.weight.bone_mass')).fill(String(newBoneMass));
    await authenticatedPage.getByLabel(t('body.weight.bmr')).fill(String(newBmr));
    await authenticatedPage.getByLabel(t('body.weight.neck')).fill(String(newNeck));
    await authenticatedPage.getByLabel(t('body.weight.chest')).fill(String(newChest));
    await authenticatedPage.getByLabel(t('body.weight.waist')).fill(String(newWaist));
    await authenticatedPage.getByLabel(t('body.weight.hips')).fill(String(newHips));
    await authenticatedPage.getByLabel(t('body.weight.bicep_r')).fill(String(newBicepR));
    await authenticatedPage.getByLabel(t('body.weight.bicep_l')).fill(String(newBicepL));
    await authenticatedPage.getByLabel(t('body.weight.thigh_r')).fill(String(newThighR));
    await authenticatedPage.getByLabel(t('body.weight.thigh_l')).fill(String(newThighL));
    await authenticatedPage.getByLabel(t('body.weight.calf_r')).fill(String(newCalfR));
    await authenticatedPage.getByLabel(t('body.weight.calf_l')).fill(String(newCalfL));
    await authenticatedPage.getByLabel(t('body.weight.notes')).fill(notes);

    await ui.submit();
    await expect(authenticatedPage.getByRole('heading', { name: t('body.weight.register_weight') })).toBeHidden({ timeout: 15000 });
    const weightCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(newWeight) }).filter({ hasText: notes }).first();
    await expect(weightCard).toBeVisible({ timeout: 10000 });
    await expect(weightCard).toContainText(newFat.toFixed(1));
    await expect(weightCard).toContainText(newMuscleKg.toFixed(1));

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('body');
    const persistedCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(newWeight) }).first();
    await expect(persistedCard).toBeVisible({ timeout: 15000 });

    await persistedCard.click();
    await expect(authenticatedPage.getByRole('heading', { name: t('body.weight.record_details') })).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.locator('#weight-date')).toHaveValue(newDate);
    await expect(authenticatedPage.getByTestId('weight-kg')).toHaveValue(String(newWeight));
    await expect(authenticatedPage.getByTestId('body-fat-pct')).toHaveValue(String(newFat));
    await expect(authenticatedPage.getByLabel(`${t('body.weight.muscle_mass')} (kg)`)).toHaveValue(String(newMuscleKg));
    await expect(authenticatedPage.getByLabel(t('body.weight.visceral_fat'))).toHaveValue(String(newVisceralFat));
    await expect(authenticatedPage.getByLabel(t('body.weight.body_water'))).toHaveValue(String(newBodyWater));
    await expect(authenticatedPage.getByLabel(t('body.weight.bone_mass'))).toHaveValue(String(newBoneMass));
    await expect(authenticatedPage.getByLabel(t('body.weight.bmr'))).toHaveValue(String(newBmr));
    await expect(authenticatedPage.getByLabel(t('body.weight.neck'))).toHaveValue(String(newNeck));
    await expect(authenticatedPage.getByLabel(t('body.weight.chest'))).toHaveValue(String(newChest));
    await expect(authenticatedPage.getByLabel(t('body.weight.waist'))).toHaveValue(String(newWaist));
    await expect(authenticatedPage.getByLabel(t('body.weight.hips'))).toHaveValue(String(newHips));
    await expect(authenticatedPage.getByLabel(t('body.weight.bicep_r'))).toHaveValue(String(newBicepR));
    await expect(authenticatedPage.getByLabel(t('body.weight.bicep_l'))).toHaveValue(String(newBicepL));
    await expect(authenticatedPage.getByLabel(t('body.weight.thigh_r'))).toHaveValue(String(newThighR));
    await expect(authenticatedPage.getByLabel(t('body.weight.thigh_l'))).toHaveValue(String(newThighL));
    await expect(authenticatedPage.getByLabel(t('body.weight.calf_r'))).toHaveValue(String(newCalfR));
    await expect(authenticatedPage.getByLabel(t('body.weight.calf_l'))).toHaveValue(String(newCalfL));
    await expect(authenticatedPage.locator('#notes')).toHaveValue(notes);

    const updatedDate = '2026-04-19';
    const updatedWeight = 77.9;
    const updatedFat = 17.4;
    const updatedMuscleKg = 35.0;
    const updatedBodyWater = 58.4;
    const updatedBmr = 1748;
    const updatedWaist = 82;
    const updatedNotes = `${notes} updated`;

    await authenticatedPage.locator('#weight-date').fill(updatedDate);
    await authenticatedPage.getByTestId('weight-kg').fill(String(updatedWeight));
    await authenticatedPage.getByTestId('body-fat-pct').fill(String(updatedFat));
    await authenticatedPage.getByLabel(`${t('body.weight.muscle_mass')} (kg)`).fill(String(updatedMuscleKg));
    await authenticatedPage.getByLabel(t('body.weight.body_water')).fill(String(updatedBodyWater));
    await authenticatedPage.getByLabel(t('body.weight.bmr')).fill(String(updatedBmr));
    await authenticatedPage.getByLabel(t('body.weight.waist')).fill(String(updatedWaist));
    await authenticatedPage.locator('#notes').fill(updatedNotes);
    await ui.submit();

    const updatedCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(updatedWeight) }).filter({ hasText: updatedNotes }).first();
    await expect(updatedCard).toBeVisible({ timeout: 15000 });
    await expect(updatedCard).toContainText(updatedFat.toFixed(1));
    await expect(updatedCard).toContainText(updatedMuscleKg.toFixed(1));
    await expect(updatedCard).toContainText(/0\.[45]/);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await ui.navigateTo('body');
    const persistedUpdatedCard = authenticatedPage.getByTestId('weight-log-card').filter({ hasText: String(updatedWeight) }).filter({ hasText: updatedNotes }).first();
    await expect(persistedUpdatedCard).toBeVisible({ timeout: 15000 });
    await expect(persistedUpdatedCard).toContainText(updatedFat.toFixed(1));
    await expect(persistedUpdatedCard).toContainText(updatedMuscleKg.toFixed(1));

    await persistedUpdatedCard.click();
    await expect(authenticatedPage.locator('#weight-date')).toHaveValue(updatedDate);
    await expect(authenticatedPage.getByTestId('weight-kg')).toHaveValue(String(updatedWeight));
    await expect(authenticatedPage.getByTestId('body-fat-pct')).toHaveValue(String(updatedFat));
    await expect(authenticatedPage.getByLabel(`${t('body.weight.muscle_mass')} (kg)`)).toHaveValue(String(updatedMuscleKg));
    await expect(authenticatedPage.getByLabel(t('body.weight.body_water'))).toHaveValue(String(updatedBodyWater));
    await expect(authenticatedPage.getByLabel(t('body.weight.bmr'))).toHaveValue(String(updatedBmr));
    await expect(authenticatedPage.getByLabel(t('body.weight.waist'))).toHaveValue(String(updatedWaist));
    await expect(authenticatedPage.locator('#notes')).toHaveValue(updatedNotes);
    await authenticatedPage.keyboard.press('Escape');

    await persistedUpdatedCard.getByTestId('btn-delete-weight').click();
    await authenticatedPage.getByTestId('confirm-accept').click();
    await expect(authenticatedPage.getByTestId('weight-log-card').filter({ hasText: updatedNotes })).toHaveCount(0);
  });
});
