import { type Page, expect } from '@playwright/test';

import { t } from './translations';

/**
 * Premium UI Actions Orchestrator
 * 
 * Encapsulates complex interactions with "Deep Space Premium" components.
 */
export class UIActions {
  private page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Universal Navigation (Desktop/Mobile)
   */
  async navigateTo(pageName: 'home' | 'dashboard' | 'workouts' | 'body' | 'chat' | 'settings') {
    const internalPageName = pageName === 'dashboard' ? 'home' : pageName;
    const desktopId = `desktop-nav-${internalPageName}`;
    const mobileId = `nav-${internalPageName}`;

    const viewport = this.page.viewportSize();
    console.log(`QA: Navigating to ${pageName}. Viewport: ${viewport?.width}x${viewport?.height}`);

    // Wait for the Nav Container to be visible first
    const desktopNav = this.page.getByTestId('desktop-nav');
    const mobileNav = this.page.getByTestId('mobile-nav');

    if (await desktopNav.isVisible()) {
      console.log('QA: Desktop Nav Container is visible');
      const item = this.page.getByTestId(desktopId);
      await expect(item).toBeVisible({ timeout: 10000 });
      await item.click();
    } else if (await mobileNav.isVisible()) {
      console.log('QA: Mobile Nav Container is visible');
      const item = this.page.getByTestId(mobileId);
      await expect(item).toBeVisible({ timeout: 10000 });
      await item.click();
    } else {
      console.warn('QA: NO NAVIGATION CONTAINER VISIBLE. Fallback to direct URL.');
      await this.page.goto(`/dashboard/${pageName === 'home' ? '' : pageName}`);
    }
    
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(1000);
  }

  /**
   * Switch between Tabs (e.g., Weight vs Nutrition in Body View)
   */
  async switchToTab(tabName: string) {
    const tabBtn = this.page.getByRole('button', { name: tabName, exact: false });
    await tabBtn.click();
    await this.page.waitForTimeout(300); // Wait for tab transition
  }

  /**
   * Interact with Premium Drawers
   */
  async openDrawer(actionLabel: string) {
    await this.page.getByRole('button', { name: actionLabel, exact: false }).click();
    // Wait for Framer Motion animation
    await this.page.waitForTimeout(500);
  }

  async closeDrawer() {
    await this.page.locator('header button').first().click();
    await this.page.waitForTimeout(500);
  }

  /**
   * Intelligent Toast Validation using real translations
   */
  async waitForToast(key: string, params?: Record<string, string | number>) {
    const expectedText = t(key, params);
    const toast = this.page.locator('[data-testid*="toast"]').or(this.page.getByRole('alert')).first();
    
    // We check if the toast contains the text, as sometimes there might be extra spacing or icons
    await expect(toast).toContainText(expectedText, { timeout: 15000 });
  }

  /**
   * Fill a Premium Form
   */
  async fillForm(fields: Record<string, string | number>) {
    // Wait for any skeleton or loading overlay to disappear
    // We check for common skeleton patterns used in Premium components
    const skeleton = this.page.locator('[data-testid*="skeleton"], .animate-pulse');
    await skeleton.waitFor({ state: 'hidden', timeout: 20000 }).catch(() => {
      console.log('QA: No skeleton found or timeout waiting for it to hide.');
    });
    
    // Extra stability wait for form hydration
    await this.page.waitForTimeout(2000); 

    for (const [label, value] of Object.entries(fields)) {
      // Find input by its associated label (PremiumFormField uses proper HTML labels)
      console.log(`QA: Filling field "${label}" with value "${value}"`);
      const input = this.page.getByLabel(label, { exact: true });
      await expect(input).toBeVisible({ timeout: 15000 });
      await input.scrollIntoViewIfNeeded();
      
      await input.fill(String(value));
      
      const afterValue = await input.inputValue();
      console.log(`QA: Value of "${label}" after standard fill: "${afterValue}"`);
    }
  }

  /**
   * Submit current form/drawer
   */
  async submit() {
    const saveText = t('common.save');
    const submitBtn = this.page.getByRole('button', { name: saveText, exact: false });
    await submitBtn.click();
  }

  /**
   * Validate Bento Widget content
   */
  async expectWidgetValue(widgetId: string, value: string | RegExp) {
    const widget = this.page.getByTestId(widgetId);
    await expect(widget).toContainText(value);
  }
}
