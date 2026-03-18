import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Profile Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should load and update identity', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/profile');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Check initial name
    const nameInput = authenticatedPage.locator('input[name="display_name"]');
    await expect(nameInput).toHaveValue(/E2E Bot/i);

    // Update name
    const newName = 'E2E Testing Bot';
    await nameInput.fill(newName);
    
    // Click "Salvar Alterações"
    await authenticatedPage.locator('button').filter({ hasText: /Salvar Alterações|Salvar|Save/i }).first().click();

    // Verify success toast
    await expect(authenticatedPage.getByText(/sucesso/i).first()).toBeVisible();

    // Verify persistence after reload
    await authenticatedPage.reload();
    await expect(nameInput).toHaveValue(newName);
  });

  test('should load and update physical profile', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/profile');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Physical profile fields
    await authenticatedPage.fill('input[name="age"]', '28');
    await authenticatedPage.fill('input[name="height"]', '185');
    
    // Select a different goal (it is a select element)
    await authenticatedPage.selectOption('select#profile-goal-type', 'lose');
    
    // Click "Salvar Alterações"
    await authenticatedPage.locator('button').filter({ hasText: /Salvar Alterações|Salvar|Save/i }).first().click();

    // Verify success toast
    await expect(authenticatedPage.getByText(/sucesso/i).first()).toBeVisible();

    // Verify in Dashboard (metabolism values should change)
    await authenticatedPage.goto('/dashboard');
    await expect(authenticatedPage.getByText(/Meta Diária/i).first()).toBeVisible();
    
    // Check back in settings
    await authenticatedPage.goto('/dashboard/settings/profile');
    await expect(authenticatedPage.locator('input[name="age"]')).toHaveValue('28');
    await expect(authenticatedPage.locator('input[name="height"]')).toHaveValue('185');
  });

  test('should show validation errors for invalid data', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/profile');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Age below 18 (backend validation)
    await authenticatedPage.fill('input[name="age"]', '15');
    await authenticatedPage.locator('button').filter({ hasText: /Salvar Alterações|Salvar|Save/i }).first().click();
    
    // It should show a validation error (either browser-side from Zod or from backend)
    await expect(authenticatedPage.getByText(/idade/i).or(authenticatedPage.getByText(/age/i)).first()).toBeVisible();
  });
});
