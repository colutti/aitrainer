import fs from 'fs';
import path from 'path';

import { test, expect } from './fixtures';
import { t } from './helpers/translations';

test.describe('Profile Photo Upload', () => {
  test('uploads, replaces, and persists a profile photo through the real settings form', async ({
    authenticatedPage,
    ui,
  }) => {
    await ui.navigateTo('settings');
    await authenticatedPage.getByRole('link', { name: t('settings.tabs.profile') }).click();

    const firstFilePath = path.resolve(process.cwd(), `tmp-e2e-profile-first-${Date.now()}.svg`);
    const secondFilePath = path.resolve(process.cwd(), `tmp-e2e-profile-second-${Date.now()}.svg`);
    const firstSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4" fill="#2563eb"/></svg>';
    const secondSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="4" height="4"><rect width="4" height="4" fill="#dc2626"/></svg>';

    try {
      fs.writeFileSync(firstFilePath, firstSvg, 'utf8');
      fs.writeFileSync(secondFilePath, secondSvg, 'utf8');

      const uploadInput = authenticatedPage.locator('input[type="file"]');
      await uploadInput.setInputFiles(firstFilePath);

      const profileImage = authenticatedPage.getByTestId('profile-form').getByRole('img', { name: 'Profile' });
      await expect(profileImage).toBeVisible({ timeout: 15000 });
      const firstUploadedSrc = await profileImage.getAttribute('src');
      expect(firstUploadedSrc).toBeTruthy();
      expect(firstUploadedSrc).toContain('data:image/svg+xml;base64');

      await uploadInput.setInputFiles(secondFilePath);
      await expect(profileImage).toBeVisible({ timeout: 15000 });
      await expect(profileImage).not.toHaveAttribute('src', firstUploadedSrc ?? '', { timeout: 15000 });

      const secondUploadedSrc = await profileImage.getAttribute('src');
      expect(secondUploadedSrc).toBeTruthy();
      expect(secondUploadedSrc).toContain('data:image/svg+xml;base64');
      expect(secondUploadedSrc).not.toBe(firstUploadedSrc);

      await authenticatedPage.reload({ waitUntil: 'networkidle' });

      const persistedImage = authenticatedPage.getByTestId('profile-form').getByRole('img', { name: 'Profile' });
      await expect(persistedImage).toBeVisible({ timeout: 15000 });
      await expect(persistedImage).toHaveAttribute('src', secondUploadedSrc);
    } finally {
      fs.rmSync(firstFilePath, { force: true });
      fs.rmSync(secondFilePath, { force: true });
    }
  });
});
