import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const OUTPUT_DIR = '/tmp/mobile-audit-screenshots';
const BASE_URL = 'http://localhost:3000';

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

const VIEWPORTS = [
  { name: '375x667_iphone-se', width: 375, height: 667 },
  { name: '390x844_iphone-14', width: 390, height: 844 },
  { name: '360x800_android', width: 360, height: 800 },
];

const ROUTES = [
  { path: '/login', name: 'login' },
  { path: '/', name: 'dashboard' },
  { path: '/workouts', name: 'workouts' },
  { path: '/nutrition', name: 'nutrition' },
  { path: '/body/weight', name: 'body-weight' },
  { path: '/chat', name: 'chat' },
  { path: '/settings/profile', name: 'settings-profile' },
  { path: '/settings/trainer', name: 'settings-trainer' },
  { path: '/settings/integrations', name: 'settings-integrations' },
  { path: '/settings/memories', name: 'settings-memories' },
];

for (const viewport of VIEWPORTS) {
  test.describe(`Mobile: ${viewport.name}`, () => {
    test.use({
      viewport: { width: viewport.width, height: viewport.height },
    });

    for (const route of ROUTES) {
      test(`${route.name}`, async ({ page }) => {
        const url = `${BASE_URL}${route.path}`;
        console.log(`📸 ${viewport.name} - ${route.name}`);

        try {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 }).catch(() => {});
          await page.waitForTimeout(1500);
        } catch (e) {
          console.log(`  ⚠️ Failed to load: ${e.message}`);
        }

        // Take screenshot
        const filename = `${viewport.name}__${route.name}.png`;
        const filepath = path.join(OUTPUT_DIR, filename);
        await page.screenshot({ path: filepath, fullPage: true });
        console.log(`  ✓ Saved: ${filename}`);
      });
    }
  });
}
