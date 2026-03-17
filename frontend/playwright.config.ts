import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// Load env variables from .env
dotenv.config({ path: '.env' });

/**
 * Playwright E2E test configuration
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    locale: 'pt-BR',
  },

  projects: [
    {
      name: 'setup',
      testMatch: /auth\.setup\.ts/,
      testIgnore: /real\/auth\.setup\.ts/,
    },
    {
      name: 'integration-setup',
      testDir: './e2e/real',
      testMatch: /auth\.setup\.ts/,
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/user.json' },
      dependencies: ['setup'],
    },
    {
      name: 'integration-public',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: { cookies: [], origins: [] }
      },
      testDir: './e2e/real',
      testMatch: /01-landing\.spec\.ts/,
      fullyParallel: false,
      workers: 1,
    },
    {
      name: 'integration',
      use: { 
        ...devices['Desktop Chrome'],
        storageState: { cookies: [], origins: [] }
      },
      testDir: './e2e/real',
      testIgnore: [/auth\.setup\.ts/, /01-landing\.spec\.ts/],
      dependencies: ['integration-setup'],
      fullyParallel: false,
      workers: 1,
    },
    {
      name: 'admin-chromium',
      use: {
        ...devices['Desktop Chrome'],
        baseURL: 'http://localhost:3001',
      },
      testMatch: /admin\.spec\.ts/,
    },
  ],

  webServer: [
    {
      command: 'npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd admin && npm run dev',
      url: 'http://localhost:3001',
      reuseExistingServer: !process.env.CI,
    },
  ],
});
