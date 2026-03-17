import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Integrations', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should connect and disconnect Hevy API', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    
    // 1. Enter fake API key
    await authenticatedPage.fill('input[placeholder*="Hevy API Key"]', 'sk_test_123456');
    await authenticatedPage.locator('button:has-text("Salvar")').first().click();
    
    // 2. Success toast
    await expect(authenticatedPage.getByText(/Conectado com sucesso/i)).toBeVisible();
    await expect(authenticatedPage.getByText('Conectado')).toBeVisible();

    // 3. Disconnect
    await authenticatedPage.locator('button:has-text("Remover")').or(authenticatedPage.locator('button:has-text("Desconectar")')).click();
    await expect(authenticatedPage.getByText(/Desconectado/i)).toBeVisible();
    await expect(authenticatedPage.getByText('Não Conectado')).toBeVisible();
  });

  test('should show Telegram integration code', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    
    // Find Telegram section and click "Gerar Código"
    await authenticatedPage.locator('button:has-text("Gerar Código")').click();
    
    // Should show a 6-digit code or similar
    await expect(authenticatedPage.getByText(/[0-9]{6}/)).toBeVisible();
  });

  test('should show CSV import result for Zepp Life', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    
    // Locate Zepp Life import and simulate file upload
    // We create a dummy CSV content
    const csvContent = 'date,weight,body_fat\n2024-03-01,80.5,18.0\n';
    const filePath = '/tmp/zepp_test.csv';
    require('fs').writeFileSync(filePath, csvContent);
    
    const [fileChooser] = await Promise.all([
      authenticatedPage.waitForEvent('filechooser'),
      authenticatedPage.locator('label:has-text("Importar CSV do Zepp Life")').click(),
    ]);
    
    await fileChooser.setFiles(filePath);
    
    // Check loading and then success
    await expect(authenticatedPage.getByText(/Importação concluída/i)).toBeVisible({ timeout: 15000 });
  });
});
