import { test, expect } from './fixtures';
import { resetOnboarding } from './helpers/cleanup';
import { t } from './helpers/translations';

test.describe('Onboarding Flow (Manual)', () => {
  test('should complete onboarding flow', async ({ page, api, browser }) => {
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

    // 1. Reset user state via API
    await resetOnboarding(api);

    // 2. Open dashboard - should redirect to onboarding
    await page.goto('/dashboard');
    
    // Wait for redirect
    await expect(page).toHaveURL(/.*onboarding/, { timeout: 15000 });
    
    // Check state
    const stepTitle = page.getByText(t('onboarding.step_2_title'));
    await expect(stepTitle).toBeVisible({ timeout: 15000 });

    // Fill Profile
    await page.getByRole('button', { name: t('onboarding.genders.male'), exact: true }).click();
    await page.getByTestId('onboarding-name').fill('E2E Manual User');
    await page.getByTestId('onboarding-age').fill('30');
    await page.getByTestId('onboarding-height').fill('180');
    await page.getByTestId('onboarding-weight').fill('80');

    // Next
    await page.getByRole('button', { name: t('onboarding.next') }).click();

    // Step 3: Plan
    await expect(page.getByText(t('onboarding.step_plan_title'))).toBeVisible();
    await page.getByText('Free', { exact: true }).click();
    await page.getByRole('button', { name: t('onboarding.next') }).click();

    // Step 4: Trainer
    await expect(page.getByText(t('onboarding.step_3_title'))).toBeVisible();
    await page.getByText('GymBro', { exact: true }).click();
    await page.getByRole('button', { name: t('onboarding.next') }).click();

    // Step 5: Integrations
    await expect(page.getByText(t('onboarding.integrations_title'))).toBeVisible();
    await page.getByRole('button', { name: t('onboarding.finish') }).click();

    // Step 6: Success
    await expect(page.getByText(t('onboarding.success_title'))).toBeVisible();
    await page.getByRole('button', { name: t('onboarding.go_to_dashboard') }).click();

    // Dashboard
    await expect(page).toHaveURL(/.*dashboard/, { timeout: 15000 });
    
    // Wait for the main layout to be visible
    await expect(page.getByTestId('desktop-nav').or(page.getByTestId('mobile-nav')).first()).toBeVisible({ timeout: 15000 });
    
    // Check for bento grid or greeting
    await expect(page.getByTestId('dashboard-bento')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Bom dia|Good morning/i)).toBeVisible({ timeout: 15000 });
  });
});
