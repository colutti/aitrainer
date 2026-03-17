import { test, expect } from './fixtures';
import { cleanupUserData } from './helpers/cleanup';

test.describe('Subscription & Billing', () => {

  test.beforeEach(async ({ api }) => {
    await cleanupUserData(api);
  });

  test('should reflect upgrade from Free to Basic via webhook', async ({ authenticatedPage, api }) => {
    await authenticatedPage.goto('/settings/subscription');
    await expect(authenticatedPage.getByText('Seu Plano: Free')).toBeVisible();

    // Simulate Stripe Webhook for successful checkout
    // Plan: Basic (price_basic_id)
    await api.post('/stripe/webhook', {
      type: 'checkout.session.completed',
      data: {
        object: {
          customer: 'cus_E2E_BOT_ID',
          amount_total: 2900,
          metadata: {
            user_email: 'e2e-bot@fityq.it',
            plan: 'Basic'
          },
          subscription: 'sub_test_basic_123'
        }
      }
    });

    // Refresh page or wait for update
    await authenticatedPage.reload();
    await expect(authenticatedPage.getByText('Seu Plano: Basic')).toBeVisible();
    await expect(authenticatedPage.getByText('GERENCIAR ASSINATURA')).toBeVisible();
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
    const sidebar = authenticatedPage.locator('aside');
    
    await expect(sidebar.getByText('PRO')).toBeVisible();
    
    // Pro limit is usually 100 or higher
    // We can check if it contains the limit text
    await expect(sidebar.getByText(/100/)).toBeVisible();
  });
});
