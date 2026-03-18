import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Subscription & Billing', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should reflect upgrade from Free to Basic via webhook', async ({ authenticatedPage, api }) => {
    await authenticatedPage.goto('/dashboard/settings/profile');
    const subscriptionTab = authenticatedPage.locator('nav').getByText(/Assinatura/i).first();
    await subscriptionTab.click();
    
    await expect(authenticatedPage.getByText(/Gratuito|Free/i).first()).toBeVisible({ timeout: 15000 });

    // Simulate Stripe Webhook for successful checkout
    await api.post('/stripe/webhook', {
      type: 'checkout.session.completed',
      data: {
        object: {
          customer: 'cus_E2E_BOT_ID',
          metadata: {
            user_email: 'e2e-bot@fityq.it',
            plan: 'Basic'
          }
        }
      }
    });

    // Refresh or re-navigate
    await authenticatedPage.goto('/dashboard/settings/profile');
    const subTab = authenticatedPage.locator('nav').getByText(/Assinatura/i).first();
    await subTab.click();
    
    await expect(authenticatedPage.getByText(/Basic/i).first()).toBeVisible({ timeout: 15000 });
    await expect(authenticatedPage.getByText(/Gerenciar/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('should show correct message limits for Pro plan', async ({ authenticatedPage, api }) => {
    // Upgrade to Pro via webhook
    await api.post('/stripe/webhook', {
      type: 'checkout.session.completed',
      data: {
        object: {
          customer: 'cus_E2E_BOT_ID',
          metadata: {
            user_email: 'e2e-bot@fityq.it',
            plan: 'Pro'
          }
        }
      }
    });

    await authenticatedPage.goto('/dashboard');
    const sidebar = authenticatedPage.locator('aside').first();
    
    await expect(sidebar.getByText(/PRO/i).first()).toBeVisible({ timeout: 15000 });
  });
});
