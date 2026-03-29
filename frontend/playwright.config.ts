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
  testIgnore: ['**/auth.setup.ts'],
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
    {
      name: 'smoke-chromium',
      testMatch: [
        '**/00-connectivity.spec.ts',
        '**/01-landing.spec.ts',
        '**/02-auth-guards.spec.ts',
        '**/03-onboarding.spec.ts',
        '**/04-navigation.spec.ts',
        '**/05-dashboard.spec.ts',
      ],
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'smoke-mobile-chromium',
      testMatch: [
        '**/00-connectivity.spec.ts',
        '**/01-landing.spec.ts',
        '**/02-auth-guards.spec.ts',
        '**/03-onboarding.spec.ts',
        '**/04-navigation.spec.ts',
        '**/05-dashboard.spec.ts',
        '**/25-mobile-core.spec.ts',
      ],
      use: { ...devices['Pixel 7'] },
    },
    {
      name: 'core-chromium',
      testMatch: [
        '**/06-profile.spec.ts',
        '**/07-workout.spec.ts',
        '**/08-nutrition.spec.ts',
        '**/09-weight.spec.ts',
        '**/10-metabolism.spec.ts',
        '**/11-memories.spec.ts',
        '**/12-chat.spec.ts',
        '**/13-settings.spec.ts',
        '**/14-integrations.spec.ts',
        '**/15-subscription.spec.ts',
        '**/16-ui-components.spec.ts',
        '**/17-dashboard-empty-states.spec.ts',
        '**/18-settings-reload.spec.ts',
        '**/30-dashboard-regressions.spec.ts',
        '**/20-landing-locale.spec.ts',
        '**/21-profile-photo.spec.ts',
        '**/22-memory-locale.spec.ts',
        '**/23-dashboard-reflection.spec.ts',
        '**/24-settings-imports.spec.ts',
        '**/26-settings-tabs.spec.ts',
      ],
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'core-mobile-chromium',
      testMatch: [
        '**/06-profile.spec.ts',
        '**/07-workout.spec.ts',
        '**/08-nutrition.spec.ts',
        '**/09-weight.spec.ts',
        '**/10-metabolism.spec.ts',
        '**/11-memories.spec.ts',
        '**/12-chat.spec.ts',
        '**/13-settings.spec.ts',
        '**/14-integrations.spec.ts',
        '**/15-subscription.spec.ts',
        '**/16-ui-components.spec.ts',
        '**/17-dashboard-empty-states.spec.ts',
        '**/18-settings-reload.spec.ts',
        '**/30-dashboard-regressions.spec.ts',
        '**/20-landing-locale.spec.ts',
        '**/21-profile-photo.spec.ts',
        '**/22-memory-locale.spec.ts',
        '**/23-dashboard-reflection.spec.ts',
        '**/24-settings-imports.spec.ts',
        '**/26-settings-tabs.spec.ts',
        '**/25-mobile-core.spec.ts',
      ],
      use: { ...devices['Pixel 7'] },
    },
    {
      name: 'demo-readonly',
      testMatch: ['**/19-demo-readonly.spec.ts'],
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox-smoke',
      testMatch: [
        '**/00-connectivity.spec.ts',
        '**/01-landing.spec.ts',
        '**/02-auth-guards.spec.ts',
        '**/03-onboarding.spec.ts',
        '**/04-navigation.spec.ts',
        '**/05-dashboard.spec.ts',
      ],
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit-smoke',
      testMatch: [
        '**/00-connectivity.spec.ts',
        '**/01-landing.spec.ts',
        '**/02-auth-guards.spec.ts',
        '**/03-onboarding.spec.ts',
        '**/04-navigation.spec.ts',
        '**/05-dashboard.spec.ts',
      ],
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'smoke-mobile-webkit',
      testMatch: [
        '**/00-connectivity.spec.ts',
        '**/01-landing.spec.ts',
        '**/02-auth-guards.spec.ts',
        '**/03-onboarding.spec.ts',
        '**/04-navigation.spec.ts',
        '**/05-dashboard.spec.ts',
        '**/25-mobile-core.spec.ts',
      ],
      use: { ...devices['iPhone 13'] },
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
