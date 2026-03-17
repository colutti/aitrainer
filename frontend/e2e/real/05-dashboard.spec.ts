import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Dashboard Features', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should display all main dashboard widgets and data correctly', async ({ authenticatedPage, api }) => {
    await authenticatedPage.setViewportSize({ width: 1440, height: 900 });
    
    // 1. Setup mock data via API
    // Add a weight log
    await api.post('/weight', {
      weight_kg: 78.5,
      body_fat_pct: 18.2,
      muscle_mass_pct: 40.5,
      date: new Date().toISOString().split('T')[0]
    });

    // Add a nutrition log
    await api.post('/nutrition/log', {
      calories: 1800,
      protein_grams: 150,
      carbs_grams: 180,
      fat_grams: 50,
      date: new Date().toISOString(),
      source: 'manual'
    });

    await authenticatedPage.goto('/dashboard');
    await authenticatedPage.waitForLoadState('networkidle');

    // 2. Verify Greeting
    await expect(authenticatedPage.getByText(/Bom dia|Boa tarde|Boa noite/)).toBeVisible();
    await expect(authenticatedPage.getByText('E2E Bot')).toBeVisible();

    // 3. Verify Stats Cards
    // TDEE/Daily target
    await expect(authenticatedPage.getByText('Meta Diária')).toBeVisible();
    await expect(authenticatedPage.getByText('2436')).toBeVisible(); // Default maintenance for our profile params

    // Consistency score
    await expect(authenticatedPage.getByText('CONSISTÊNCIA')).toBeVisible();
    
    // 4. Verify Macro Progress
    await expect(authenticatedPage.getByText('PROTEÍNA')).toBeVisible();
    await expect(authenticatedPage.getByText('126g')).toBeVisible(); // Target protein for 180cm, 80kg male maintenance

    // 5. Verify Recent Activities
    // We added 1 weight and 1 nutrition log
    await expect(authenticatedPage.getByText('Pesagem')).toBeVisible();
    await expect(authenticatedPage.getByText('Refeição')).toBeVisible();

    // 6. Verify WidgetPRs (should show "Dados de força insuficientes" if no workouts)
    await expect(authenticatedPage.getByText(/Dados de Forca Insuficientes/i)).toBeVisible();
  });

  test('should show payment success toast notification', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard?payment=success');
    
    // Check for success toast
    // The translation key is landing.subscription.payment_success_message
    // In pt-BR it's something like "Pagamento realizado com sucesso"
    await expect(authenticatedPage.locator('.bg-green-500\\/10')).toBeVisible();
    await expect(authenticatedPage.getByText(/sucesso/i)).toBeVisible();
  });

  test('should show payment cancelled toast notification', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard?payment=cancelled');
    
    // Check for info toast
    await expect(authenticatedPage.locator('.bg-blue-500\\/10')).toBeVisible();
    await expect(authenticatedPage.getByText(/cancelado/i)).toBeVisible();
  });
});
