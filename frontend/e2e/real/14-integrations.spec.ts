import * as fs from 'fs';
import * as path from 'path';

import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Integrations', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should connect and disconnect Hevy API', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // 1. Enter fake API key
    const input = authenticatedPage.locator('input#hevy-key').first();
    await expect(input).toBeVisible({ timeout: 15000 });
    await input.fill('sk_test_123456');
    
    // Hevy Save button text is "Confirmar"
    await authenticatedPage.locator('button').filter({ hasText: /Confirmar/i }).first().click({ force: true });
    
    // 2. Success toast or active state
    await expect(authenticatedPage.getByText(/sucesso|ativo/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('should show Telegram integration code', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');
    
    // Find Telegram section and click "Gerar Código"
    const generateBtn = authenticatedPage.locator('button').filter({ hasText: /Gerar/i }).first();
    await expect(generateBtn).toBeVisible({ timeout: 15000 });
    await generateBtn.click({ force: true });
    
    // Should show a 6-digit code (mocked as 123456 in VB)
    await expect(authenticatedPage.getByText(/123456/).first()).toBeVisible({ timeout: 10000 });
  });

  test('should show CSV import result for Zepp Life', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/dashboard/settings/integrations');
    await authenticatedPage.waitForLoadState('networkidle');
    
    const csvContent = 'date,weight,body_fat\n2024-03-01,80.5,18.0\n';
    const filePath = path.join('/tmp', `zepp_test_${Date.now()}.csv`);
    fs.writeFileSync(filePath, csvContent);
    
    // Find Zepp Life section more robustly
    const zeppSection = authenticatedPage.locator('div').filter({ hasText: /Zepp/ }).last();
    const uploadLabel = zeppSection.locator('label').first();
    
    await expect(uploadLabel).toBeVisible({ timeout: 15000 });

    const fileChooserPromise = authenticatedPage.waitForEvent('filechooser');
    await uploadLabel.click({ force: true });
    const fileChooser = await fileChooserPromise;
    
    await fileChooser.setFiles(filePath);
    
    // Check success
    await expect(authenticatedPage.getByText(/sucesso|concluída/i).first()).toBeVisible({ timeout: 15000 });
  });
});
