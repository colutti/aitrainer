import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Load env variables from .env and .env.e2e
dotenv.config({ path: '.env' });
dotenv.config({ path: '.env.e2e' });

/**
 * Playwright E2E test configuration
 * Runs against the real backend stack.
 */
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000';
const shouldManageWebServer = process.env.PLAYWRIGHT_SKIP_WEB_SERVER !== '1';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['html', { open: 'never', outputFolder: 'playwright-report' }], ['list']],
  use: {
    baseURL,
    trace: 'on-first-retry',
    locale: 'pt-BR',
    // Default to Desktop for business flow stability
    viewport: { width: 1280, height: 720 },
    launchOptions: {
      args: ['--disable-web-security']
    }
  },

  projects: [
    { name: 'setup', testMatch: /auth\.setup\.ts/ },
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json' 
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        storageState: 'playwright/.auth/user.json' 
      },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        storageState: 'playwright/.auth/user.json' 
      },
      dependencies: ['setup'],
    },
  ],

  webServer: shouldManageWebServer
    ? [
        {
          command: 'npm run dev',
          url: baseURL,
          reuseExistingServer: true,
          timeout: 120000,
        },
      ]
    : undefined,
});
