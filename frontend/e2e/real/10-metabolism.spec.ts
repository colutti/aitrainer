import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Metabolism Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should show metabolism stats and period selector', async ({ authenticatedPage, api }) => {
    // 1. Seed data to ensure metabolism can be calculated
    const now = new Date();
    // 7 days of logs
    for (let i = 0; i < 7; i++) {
       const date = new Date(now);
       date.setDate(date.getDate() - i);
       const dateStr = date.toISOString().split('T')[0];
       
       await api.post('/weight', { weight_kg: 80 - (i * 0.1), date: dateStr });
       await api.post('/nutrition/log', { 
         calories: 2000, 
         protein_grams: 150,
         carbs_grams: 200,
         fat_grams: 50,
         date: date.toISOString() 
       });
    }

    await authenticatedPage.goto('/dashboard/metabolism');
    await authenticatedPage.waitForLoadState('networkidle');

    // 2. Check main stats
    await expect(authenticatedPage.getByText('Seu TDEE Atual')).toBeVisible();
    await expect(authenticatedPage.getByText('Meta de Calorias')).toBeVisible();
    
    // 3. Check Confidence Badge
    // With 7 days of data, it might be Low or Medium
    await expect(authenticatedPage.getByText(/Confian.a/i)).toBeVisible();

    // 4. Test Period Selector
    // The component usually has buttons like "2 sem", "4 sem", etc.
    const periods = ['2 sem', '4 sem', '8 sem', '12 sem'];
    for (const p of periods) {
      const btn = authenticatedPage.getByRole('button', { name: p });
      if (await btn.isVisible()) {
        await btn.click();
        // Just verify it doesn't crash and is still on page
        await expect(authenticatedPage.getByText('Seu TDEE Atual')).toBeVisible();
      }
    }
  });
});
