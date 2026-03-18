import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Load env variables from .env
dotenv.config({ path: '.env' });

/**
 * Playwright E2E test configuration
 * Focused on the stable Mocked VirtualBackend suite.
 */
export default defineConfig({
  testDir: './e2e/real', // Focus on the fixed tests
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    locale: 'pt-BR',
  },

  projects: [
    {
      name: 'e2e',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: { cookies: [], origins: [] } 
      },
      testIgnore: [/auth\.setup\.ts/],
    },
  ],

  webServer: [
    {
      command: 'npm run preview -- --port 3000',
      url: 'http://localhost:3000',
      reuseExistingServer: false,
      timeout: 60000,
    },
  ],
});
