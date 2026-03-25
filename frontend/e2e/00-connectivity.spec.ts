import { test, expect } from '@playwright/test';

test('Basic connectivity: Check title and root', async ({ page }) => {
  await page.goto('/login', { waitUntil: 'load' });
  const title = await page.title();
  console.log('PAGE TITLE:', title);
  
  const rootExists = await page.locator('#root').count();
  console.log('ROOT EXISTS:', rootExists > 0);
  
  const bodyHtml = await page.innerHTML('body');
  console.log('BODY HTML LENGTH:', bodyHtml.length);
  // Log a bit of body to see if there's script tags but no content
  console.log('BODY HTML SNIPPET:', bodyHtml.substring(0, 200));
  
  await expect(page).toHaveTitle(/FityQ/i);
});
