import fs from 'fs';
import path from 'path';

import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Profile Photo Upload', () => {
  test('uploads a profile photo through the real settings form', async ({ authenticatedPage, ui }) => {
    await ui.navigateTo('settings');
    await authenticatedPage.getByRole('link', { name: t('settings.tabs.profile') }).click();

    const filePath = path.resolve(process.cwd(), `tmp-e2e-profile-${Date.now()}.png`);
    const pngBase64 =
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2fE6QAAAAASUVORK5CYII=';

    try {
      fs.writeFileSync(filePath, Buffer.from(pngBase64, 'base64'));

      const uploadInput = authenticatedPage.locator('input[type="file"]');
      await uploadInput.setInputFiles(filePath);

      const profileImage = authenticatedPage.getByTestId('profile-form').getByRole('img', { name: 'Profile' });
      await expect(profileImage).toBeVisible({ timeout: 15000 });
      await expect(profileImage).toHaveAttribute(
        'src',
        /data:image\/png;base64/
      );
    } finally {
      fs.rmSync(filePath, { force: true });
    }
  });
});
