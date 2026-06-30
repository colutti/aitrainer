import type { Locator } from '@playwright/test';

import { test, expect } from './fixtures';
import { t } from './helpers/translations';

async function clearNumberInput(field: Locator) {
  await field.click();
  await field.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');
  await field.press('Backspace');
  await expect(field).toHaveValue('');
}

test.describe('Nutrition Feature', () => {
  test('should verify nutrition page elements and empty state', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/nutrition', { waitUntil: 'networkidle' });

    const addButton = authenticatedPage.getByRole('button', { name: t('nutrition.register_meal') }).first();
    await expect(addButton).toBeVisible({ timeout: 10000 });
  });

  test('should open nutrition drawer when clicking to register meal', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/nutrition', { waitUntil: 'networkidle' });

    const addButton = authenticatedPage.getByRole('button', { name: t('nutrition.register_meal') }).first();
    await addButton.click();

    await expect(authenticatedPage.getByRole('heading', { name: /Registrar Refei..o|Register Meal|Registrar Comida/i })).toBeVisible({
      timeout: 15000,
    });
    await expect(authenticatedPage.locator('#calories')).toBeVisible({ timeout: 15000 });
  });

  test('should create, edit, reload and delete a nutrition log through the UI', async ({ authenticatedPage, ui, api }) => {
    await authenticatedPage.goto('/dashboard/nutrition', { waitUntil: 'networkidle' });

    const initialDate = '2026-04-16';
    const initialCalories = 612;
    const initialProtein = 41;
    const initialCarbs = 72;
    const initialFat = 19;
    const initialFiber = 24;
    const initialSodium = 1800;

    await ui.openDrawer(t('nutrition.register_meal'));
    await authenticatedPage.locator('#nutrition-date').fill(initialDate);
    await authenticatedPage.getByLabel(t('body.nutrition.calories')).fill(String(initialCalories));
    await authenticatedPage.getByLabel(t('body.nutrition.protein')).fill(String(initialProtein));
    await authenticatedPage.getByLabel(t('body.nutrition.carbs')).fill(String(initialCarbs));
    await authenticatedPage.getByLabel(t('body.nutrition.fat')).fill(String(initialFat));
    await authenticatedPage.getByLabel(t('body.nutrition.fiber')).fill(String(initialFiber));
    await authenticatedPage.getByLabel(t('body.nutrition.sodium')).fill(String(initialSodium));
    await ui.submit();

    const createdCard = authenticatedPage.getByTestId('nutrition-log-card').filter({ hasText: `${initialCalories}` }).first();
    await expect(createdCard).toBeVisible({ timeout: 15000 });
    await expect(createdCard).toContainText(`${initialProtein}g`);

    await createdCard.getByLabel(/Editar|Edit/i).click();
    await expect(authenticatedPage.getByRole('heading', { name: /Editar Refei..o|Edit Meal|Editar Comida/i })).toBeVisible({
      timeout: 15000,
    });

    const updatedDate = '2026-04-17';
    const updatedCalories = 730;
    const updatedProtein = 55;
    const updatedCarbs = 64;
    const updatedFat = 23;
    const updatedFiber = 31;
    const updatedSodium = 1450;

    await authenticatedPage.locator('#nutrition-date').fill(updatedDate);
    await authenticatedPage.getByLabel(t('body.nutrition.calories')).fill(String(updatedCalories));
    await authenticatedPage.getByLabel(t('body.nutrition.protein')).fill(String(updatedProtein));
    await authenticatedPage.getByLabel(t('body.nutrition.carbs')).fill(String(updatedCarbs));
    await authenticatedPage.getByLabel(t('body.nutrition.fat')).fill(String(updatedFat));
    await authenticatedPage.getByLabel(t('body.nutrition.fiber')).fill(String(updatedFiber));
    await authenticatedPage.getByLabel(t('body.nutrition.sodium')).fill(String(updatedSodium));
    await ui.submit();

    const updatedCard = authenticatedPage.getByTestId('nutrition-log-card').filter({ hasText: `${updatedCalories}` }).first();
    await expect(updatedCard).toBeVisible({ timeout: 15000 });
    await expect(updatedCard).toContainText(`${updatedProtein}g`);
    await expect(updatedCard).toContainText(`${updatedCarbs}g`);
    await expect(updatedCard).toContainText(`${updatedFat}g`);

    const afterUpdateResponse = await api.get('/nutrition/list?page=1&page_size=20');
    expect(afterUpdateResponse.ok()).toBeTruthy();
    const afterUpdatePayload = await afterUpdateResponse.json() as {
      logs: {
        id: string;
        date: string;
        calories: number;
        fiber_grams?: number | null;
        sodium_mg?: number | null;
      }[];
    };
    const updatedLog = afterUpdatePayload.logs.find((log) => log.calories === updatedCalories);
    expect(updatedLog).toBeTruthy();
    expect(updatedLog?.date).toContain(updatedDate);
    expect(updatedLog?.fiber_grams).toBe(updatedFiber);
    expect(updatedLog?.sodium_mg).toBe(updatedSodium);

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/nutrition', { waitUntil: 'networkidle' });
    const persistedCard = authenticatedPage.getByTestId('nutrition-log-card').filter({ hasText: `${updatedCalories}` }).first();
    await expect(persistedCard).toBeVisible({ timeout: 15000 });

    await persistedCard.click();
    await expect(authenticatedPage.getByRole('heading', { name: t('body.nutrition.record_details') })).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(`${updatedProtein}g`).last()).toBeVisible();
    await expect(authenticatedPage.getByText(`${updatedCarbs}g`).last()).toBeVisible();
    await expect(authenticatedPage.getByText(`${updatedFat}g`).last()).toBeVisible();
    await expect(authenticatedPage.getByText(`${updatedFiber}g`).last()).toBeVisible();
    await expect(authenticatedPage.getByText(`${updatedSodium}mg`).last()).toBeVisible();
    await expect(
      authenticatedPage.locator('span').filter({ hasText: /17\/04\/2026|04\/17\/2026|17-04-2026/ }).last()
    ).toBeVisible();
    await authenticatedPage.keyboard.press('Escape');

    await persistedCard.getByLabel(/Editar|Edit/i).click();
    await expect(authenticatedPage.getByRole('heading', { name: /Editar Refei..o|Edit Meal|Editar Comida/i })).toBeVisible({
      timeout: 15000,
    });
    await clearNumberInput(authenticatedPage.getByLabel(t('body.nutrition.fiber')));
    await clearNumberInput(authenticatedPage.getByLabel(t('body.nutrition.sodium')));
    const clearRequestPromise = authenticatedPage.waitForRequest((request) =>
      request.method() === 'PUT' && request.url().includes('/api/nutrition/log/')
    );
    await ui.submit();
    const clearRequest = await clearRequestPromise;
    const clearRequestPayload = clearRequest.postDataJSON() as {
      fiber_grams?: number | null;
      sodium_mg?: number | null;
      date?: string;
    };
    expect(clearRequestPayload.date).toContain(updatedDate);
    expect(clearRequestPayload.fiber_grams ?? null).toBeNull();
    expect(clearRequestPayload.sodium_mg ?? null).toBeNull();

    const clearedCard = authenticatedPage.getByTestId('nutrition-log-card').filter({ hasText: `${updatedCalories}` }).first();
    await expect(clearedCard).toBeVisible({ timeout: 15000 });

    const afterClearResponse = await api.get('/nutrition/list?page=1&page_size=20');
    expect(afterClearResponse.ok()).toBeTruthy();
    const afterClearPayload = await afterClearResponse.json() as {
      logs: {
        id: string;
        date: string;
        calories: number;
        fiber_grams?: number | null;
        sodium_mg?: number | null;
      }[];
    };
    const clearedLog = afterClearPayload.logs.find((log) => log.calories === updatedCalories);
    expect(clearedLog).toBeTruthy();
    expect(clearedLog?.date).toContain(updatedDate);
    expect(clearedLog?.fiber_grams ?? null).toBeNull();
    expect(clearedLog?.sodium_mg ?? null).toBeNull();

    await authenticatedPage.reload({ waitUntil: 'networkidle' });
    await authenticatedPage.goto('/dashboard/nutrition', { waitUntil: 'networkidle' });
    const clearedPersistedCard = authenticatedPage.getByTestId('nutrition-log-card').filter({ hasText: `${updatedCalories}` }).first();
    await expect(clearedPersistedCard).toBeVisible({ timeout: 15000 });
    await clearedPersistedCard.click();
    await expect(authenticatedPage.getByRole('heading', { name: t('body.nutrition.record_details') })).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText('-').first()).toBeVisible();
    await expect(authenticatedPage.getByText('-').last()).toBeVisible();
    await authenticatedPage.keyboard.press('Escape');

    await clearedPersistedCard.getByTestId('btn-delete-nutrition').click();
    await authenticatedPage.getByTestId('confirm-accept').click();
    await expect(authenticatedPage.getByTestId('nutrition-log-card').filter({ hasText: `${updatedCalories}` })).toHaveCount(0);
  });
});
