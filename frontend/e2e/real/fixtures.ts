import { execSync } from 'child_process';
import fs from 'fs';

import { test as base, expect, type Page } from '@playwright/test';

import { ApiClient } from './helpers/api-client';

/**
 * Interface for our custom fixtures
 */
interface MyFixtures {
  api: ApiClient;
  authenticatedPage: Page;
}

export const test = base.extend<MyFixtures>({
  // Direct API client fixture
  // eslint-disable-next-line no-empty-pattern
  api: async ({ }, use) => {
    let token = '';
    
    try {
      // Run the setup script in the backend container to get a fresh E2E bot token
      console.log('DEBUG: Running setup_e2e_user.py script...');
      const output = execSync('podman exec personal_backend_1 python /app/scripts/setup_e2e_user.py').toString();
      
      // The script might have debug logs in stderr, we only want the JSON from stdout
      const lines = output.trim().split('\n');
      const jsonLine = lines.find(line => line.trim().startsWith('{'));
      
      if (jsonLine) {
        const data = JSON.parse(jsonLine);
        token = data.token;
        console.log(`DEBUG: Obtained fresh token for ${data.email}`);
      } else {
        console.error('DEBUG: Failed to find JSON in script output:', output);
      }
    } catch (error) {
      console.error('DEBUG: Error calling setup_e2e_user.py:', error);
      
      // Fallback to existing auth file if script fails
      const authFile = 'playwright/.auth/integration.json';
      if (fs.existsSync(authFile)) {
        console.log('DEBUG: Falling back to integration.json');
        const auth = JSON.parse(fs.readFileSync(authFile, 'utf-8'));
        const origins = auth.origins as any[];
        const localStorageData = origins.find((o: any) => o.origin.includes('localhost'))?.localStorage;
        token = localStorageData?.find((i: any) => i.name === 'auth_token')?.value || '';
      }
    }

    const client = new ApiClient(token);
    await use(client);
  },

  // Authenticated page fixture
  authenticatedPage: async ({ page, api }, use) => {
    const token = api.token;
    const email = 'e2e-bot@fityq.it'; // Fixed E2E bot email
    const tourKey = `dashboard-main-${email}`;

    if (token) {
      console.log(`DEBUG: Using addInitScript to inject token for ${email}`);
      // Inject token BEFORE any page scripts run
      await page.addInitScript(({ t, k }: { t: string; k: string }) => {
        window.localStorage.setItem('auth_token', t);
        window.localStorage.setItem(`has_seen_tour_${k}`, 'true');
        window.localStorage.setItem('has_seen_tour_dashboard-main-guest', 'true');
        window.localStorage.setItem('i18nextLng', 'pt-BR');
      }, { t: token, k: tourKey });
    } else {
      console.error('DEBUG: No token available for authenticatedPage fixture!');
    }
    
    // Add console listener for debugging
    page.on('console', (msg) => {
      if (msg.type() === 'error' || msg.type() === 'warning') {
        console.log(`BROWSER [${msg.type()}]: ${msg.text()}`);
      }
    });

    // Set desktop viewport BEFORE navigating so sidebar is visible (TailwindCSS lg:flex = 1024px+)
    await page.setViewportSize({ width: 1440, height: 900 });
    
    // Navigate directly to dashboard
    console.log('DEBUG: Navigating to /dashboard');
    await page.goto('/dashboard');
    
    // Wait for the app to initialize
    await page.waitForLoadState('networkidle');
    
    await use(page);
  }
});

export { expect };
