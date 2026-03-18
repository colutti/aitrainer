import { test, expect } from './fixtures';

test.describe('Onboarding Flow', () => {
  
  test('should complete the full onboarding flow for an authenticated user', async ({ authenticatedPage, api }) => {
    // 1. Reset user to incomplete onboarding
    await api.post('/user/update_profile', {
      gender: 'Masculino',
      age: 30,
      height: 175,
      weight: 80,
      goal_type: 'maintain',
      weekly_rate: 0,
      onboarding_completed: false
    });
    
    // 2. Go to dashboard, should redirect to onboarding
    await authenticatedPage.goto('/dashboard');
    await expect(authenticatedPage).toHaveURL(/.*onboarding/, { timeout: 20000 });
    
    // Step 2: Profile Info
    // Use generic selectors if IDs fail
    await authenticatedPage.locator('input').filter({ hasAttribute: ['name', 'name'] }).or(authenticatedPage.locator('#name')).first().fill('E2E Tester');
    await authenticatedPage.getByRole('button', { name: /Masculino/i }).first().click();
    await authenticatedPage.locator('input#age').fill('25');
    await authenticatedPage.locator('input#height').fill('175');
    await authenticatedPage.locator('input#weight').fill('75');
    
    await authenticatedPage.getByRole('button', { name: /Próximo/i }).first().click();
    
    // Step 3: Plan Selection
    await expect(authenticatedPage.getByText(/Plano/i).first()).toBeVisible();
    await authenticatedPage.getByText(/Free/i).first().click();
    await authenticatedPage.getByRole('button', { name: /Próximo/i }).first().click();
    
    // Step 4: Trainer Selection
    await expect(authenticatedPage.getByText(/Treinador/i).first()).toBeVisible();
    await authenticatedPage.getByText(/GymBro/i).first().click();
    await authenticatedPage.getByRole('button', { name: /Próximo/i }).first().click();
    
    // Step 5: Integrations
    await expect(authenticatedPage.getByText(/Evolução/i).first()).toBeVisible();
    // Button text can be "Finalizar" or "Finalizar Onboarding"
    await authenticatedPage.getByRole('button', { name: /Finalizar/i }).first().click();

    // Step 6: Success
    await expect(authenticatedPage.getByText(/Pronto/i).first()).toBeVisible({ timeout: 15000 });
    await authenticatedPage.getByRole('button', { name: /Dashboard/i }).first().click();

    // Final verification
    await expect(authenticatedPage).toHaveURL(/.*dashboard/, { timeout: 15000 });
    
    const res = await api.get('/user/me');
    const user = await res.json();
    expect(user.onboarding_completed).toBe(true);
  });
});
