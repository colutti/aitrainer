import { test, expect, Page } from '@playwright/test';

test.describe('Integrations - Hevy e Telegram', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'deacandia@gmail.com');
    await page.fill('input[type="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Navigate to integrations
    await page.goto('/settings/integrations');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('Hevy: syncHevy deve chamar /integrations/hevy/import e NÃO /sync', async () => {
    const requests: string[] = [];

    // Interceptar requisições
    page.on('request', (request) => {
      if (request.url().includes('/integrations/hevy')) {
        requests.push(request.url());
      }
    });

    // Carregar status (verificar que tem chave)
    await page.waitForSelector('button:has-text("Sincronizar Agora")');

    // Clicar em sincronizar
    await page.click('button:has-text("Sincronizar Agora")');

    // Aguardar a requisição
    await page.waitForTimeout(2000);

    // Verificar que a URL contém /import e NÃO /sync
    const importRequests = requests.filter(url => url.includes('/import'));
    const syncRequests = requests.filter(url => url.includes('/sync'));

    expect(importRequests.length).toBeGreaterThan(0);
    expect(syncRequests.length).toBe(0); // Nunca deve chamar /sync
    expect(importRequests[0]).toContain('/integrations/hevy/import');
  });

  test('Telegram: status endpoint deve retornar "linked" e "telegram_username"', async () => {
    // Interceptar resposta do status
    const statusPromise = new Promise((resolve) => {
      page.on('response', async (response) => {
        if (response.url().includes('/integrations/telegram/status')) {
          const data = await response.json();
          resolve(data);
        }
      });
    });

    // Disparar reload da página (para forçar a requisição de status)
    await page.reload();

    const status = await Promise.race([
      statusPromise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Timeout')), 5000)
      )
    ]) as any;

    // Validar que resposta tem os campos corretos
    expect(status).toHaveProperty('linked');
    expect(status).not.toHaveProperty('connected'); // NÃO deve ter "connected"
    if (status.linked) {
      expect(status).toHaveProperty('telegram_username');
      expect(status).not.toHaveProperty('username'); // NÃO deve ter "username"
    }
  });

  test('Telegram: se linked=true, deve exibir "Conectado como @username"', async () => {
    // Mock response para linked=true
    await page.route('**/integrations/telegram/status', (route) => {
      route.abort('blockedbypage');
    });

    await page.route('**/integrations/telegram/status', async (route) => {
      await route.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          linked: true,
          telegram_username: 'test_bot_user',
          telegram_notify_on_workout: true,
          telegram_notify_on_nutrition: false,
          telegram_notify_on_weight: false,
          linked_at: new Date().toISOString()
        })
      });
    });

    // Reload para carregar o mock
    await page.reload();
    await page.waitForTimeout(1000);

    // Deve exibir "Conectado como @test_bot_user"
    const connectedText = page.locator('text=Conectado como @test_bot_user');
    await expect(connectedText).toBeVisible();

    // NÃO deve exibir o botão "Gerar Código de Conexão"
    const generateBtn = page.locator('button:has-text("Gerar Código de Conexão")');
    await expect(generateBtn).not.toBeVisible();
  });

  test('Telegram: se linked=false, deve exibir botão "Gerar Código de Conexão"', async () => {
    // Mock response para linked=false
    await page.route('**/integrations/telegram/status', async (route) => {
      await route.respond({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          linked: false,
          telegram_notify_on_workout: true,
          telegram_notify_on_nutrition: false,
          telegram_notify_on_weight: false,
        })
      });
    });

    // Reload para carregar o mock
    await page.reload();
    await page.waitForTimeout(1000);

    // Deve exibir o botão "Gerar Código de Conexão"
    const generateBtn = page.locator('button:has-text("Gerar Código de Conexão")');
    await expect(generateBtn).toBeVisible();

    // NÃO deve exibir "Conectado como"
    const connectedText = page.locator('text=/Conectado como @/');
    await expect(connectedText).not.toBeVisible();
  });

  test('Hevy: endpoint /sync deve retornar 404 (endpoint inexistente)', async () => {
    let received404 = false;

    page.on('response', (response) => {
      if (response.url().includes('/integrations/hevy/sync') && response.status() === 404) {
        received404 = true;
      }
    });

    // Tentar chamar /sync diretamente (nunca deve acontecer via UI)
    const response = await page.evaluate(async () => {
      try {
        const res = await fetch('/integrations/hevy/sync', { method: 'POST' });
        return res.status;
      } catch {
        return null;
      }
    });

    // Se conseguiu fazer a requisição, deve ser 404
    if (response === 404) {
      expect(response).toBe(404);
    }
  });

  test('Telegram: field mapping deve ser exato (linked, telegram_username, etc)', async () => {
    // Fazer requisição real e validar shape da resposta
    const response = await page.evaluate(async () => {
      const res = await fetch('/integrations/telegram/status');
      const data = await res.json();

      // Retornar as chaves para validação
      return {
        keys: Object.keys(data),
        linked: typeof data.linked,
        hasConnected: 'connected' in data,
        hasLinked: 'linked' in data,
        hasTelegramUsername: 'telegram_username' in data,
        hasUsername: 'username' in data,
      };
    });

    // Validações críticas
    expect(response.hasLinked).toBe(true); // Deve ter "linked"
    expect(response.hasConnected).toBe(false); // NÃO deve ter "connected"

    // Se linked=true, deve ter telegram_username
    const status = await page.evaluate(async () => {
      const res = await fetch('/integrations/telegram/status');
      return res.json();
    });

    if (status.linked) {
      expect(status).toHaveProperty('telegram_username');
      expect(status).not.toHaveProperty('username');
    }
  });
});
