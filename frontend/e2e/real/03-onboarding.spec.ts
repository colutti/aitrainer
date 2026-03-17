import { test, expect } from './fixtures';

test.describe('Onboarding Flow', () => {
  
  test('should complete the full onboarding flow for an authenticated user', async ({ authenticatedPage, api }) => {
    // 1. Reset user to incomplete onboarding
    // Need full profile for /user/update_profile to avoid 422
    const meRes = await api.get('/user/me');
    const fullProfile = await meRes.json();
    
    // Filter only fields accepted by UserProfileInput
    const inputFields = [
      'gender', 'age', 'weight', 'height', 'goal_type', 'target_weight', 
      'weekly_rate', 'notes', 'onboarding_completed'
    ];
    const updateData: any = {};
    for (const field of inputFields) {
      if (fullProfile[field] !== undefined && fullProfile[field] !== null) {
        updateData[field] = fullProfile[field];
      }
    }
    
    // Ensure mandatory fields for UserProfileInput are present
    if (!updateData.gender) updateData.gender = 'Masculino';
    if (!updateData.age) updateData.age = 30;
    if (!updateData.height) updateData.height = 175;
    if (!updateData.goal_type) updateData.goal_type = 'maintain';
    if (!updateData.weekly_rate) updateData.weekly_rate = 0.5;
    
    updateData.onboarding_completed = false;
    
    const updateRes = await api.post('/user/update_profile', updateData);
    if (!updateRes.ok()) {
      const error = await updateRes.json();
      console.error('Update Profile failed:', JSON.stringify(error, null, 2));
    }
    expect(updateRes.status()).toBe(200);
    
    // 2. Go to dashboard, should redirect to onboarding
    await authenticatedPage.goto('/dashboard');
    await expect(authenticatedPage).toHaveURL(/.*onboarding/);
    
    // Step 2: Profile Info (Step 2 in code)
    await authenticatedPage.fill('#name', 'E2E Tester');
    await authenticatedPage.click('button:has-text("Masculino")');
    await authenticatedPage.fill('#age', '25');
    await authenticatedPage.fill('#height', '175');
    await authenticatedPage.fill('#weight', '75');
    
    // Use the specific "Próximo" button in the Profile step
    await authenticatedPage.click('button:has-text("Próximo")');
    
    // Step 3: Plan Selection
    await expect(authenticatedPage.getByText('Escolha seu Plano')).toBeVisible();
    await authenticatedPage.click('text=Free');
    await authenticatedPage.click('button:has-text("Próximo")');
    
    // Step 4: Trainer Selection
    await expect(authenticatedPage.getByText('Escolha seu Treinador')).toBeVisible();
    await authenticatedPage.click('text=GymBro');
    // Button text is "Próximo" but it calls handleSubmitProfile which goes to step 5 or 6
    await authenticatedPage.click('button:has-text("Próximo")');
    
    // Step 5: Integrations (we skip it and just click "Finalizar")
    await expect(authenticatedPage.getByText('Turbine sua Evolução')).toBeVisible();
    await authenticatedPage.click('button:has-text("Finalizar Cadastro")');

    // Step 6: Success
    await expect(authenticatedPage.getByText('Tudo Pronto!')).toBeVisible();
    await authenticatedPage.click('button:has-text("Ir para o Dashboard")');

    // Final verification: Should be on dashboard
    await expect(authenticatedPage).toHaveURL(/.*dashboard/, { timeout: 15000 });
    
    // Verify in DB via API
    const res = await api.get('/user/me');
    const user = await res.json();
    expect(user.onboarding_completed).toBe(true);
    expect(user.name).toBe('E2E Tester');
  });
});
