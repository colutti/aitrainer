import { expect, type Page, type TestInfo } from '@playwright/test';

export interface E2EUserCredentials {
  name: string;
  email: string;
  password: string;
}

export interface OnboardingProfile {
  name?: string;
  gender?: 'Masculino' | 'Feminino';
  age?: number;
  height?: number;
  weight?: number;
  trainerType?: 'gymbro' | 'atlas' | 'luna' | 'sargento' | 'sofia';
  subscriptionPlan?: 'Free' | 'Basic' | 'Pro' | 'Premium';
}

export function buildE2EUserCredentials(testInfo: TestInfo, suffix = 'user'): E2EUserCredentials {
  const slug = testInfo.titlePath
    .join('-')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 36) || 'spec';

  const email = `e2e-${slug}-${testInfo.repeatEachIndex}-${suffix}@fityq.it`;
  const baseName = `E2E ${testInfo.titlePath.at(-1) ?? 'User'}`.trim();
  const name = baseName.slice(0, 50);

  return {
    name,
    email,
    password: 'FityqDemo!2026',
  };
}

export async function registerViaUi(page: Page, user: E2EUserCredentials) {
  await page.goto('/login?mode=register', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: /Registro/i }).click();
  await page.getByTestId('register-name').fill(user.name);
  await page.getByTestId('register-email').fill(user.email);
  await page.getByTestId('register-password').fill(user.password);
  await page.getByTestId('register-confirm-password').fill(user.password);
  await page.getByRole('button', { name: /Criar Conta/i }).click();
  await expect(page).toHaveURL(/\/onboarding(?:\?.*)?$/, { timeout: 20000 });
  await expect(page.getByText(/Your Profile|Seu Perfil|Tu perfil/i)).toBeVisible({ timeout: 20000 });
}

export async function completeOnboardingViaUi(page: Page, profile: OnboardingProfile = {}) {
  const name = profile.name ?? 'E2E User';
  const gender = profile.gender ?? 'Masculino';
  const age = profile.age ?? 30;
  const height = profile.height ?? 180;
  const weight = profile.weight ?? 80;
  const trainerType = profile.trainerType ?? 'gymbro';
  const subscriptionPlan = profile.subscriptionPlan ?? 'Free';

  if (!page.url().includes('/onboarding')) {
    await page.goto('/onboarding', { waitUntil: 'networkidle' });
  }
  await expect(page.getByText(/Your Profile|Seu Perfil|Tu perfil/i)).toBeVisible({ timeout: 20000 });
  await page.getByRole('button', { name: new RegExp(gender, 'i') }).click();
  await page.getByTestId('onboarding-name').fill(name);
  await page.getByTestId('onboarding-age').fill(String(age));
  await page.getByTestId('onboarding-height').fill(String(height));
  await page.getByTestId('onboarding-weight').fill(String(weight));
  await page.getByRole('button', { name: /Próximo|Next/i }).click();

  await page.getByText(subscriptionPlan, { exact: true }).click();
  await page.getByRole('button', { name: /Próximo|Next/i }).click();

  await page.getByText(new RegExp(`^${trainerType}$`, 'i')).click();
  await page.getByRole('button', { name: /Próximo|Next/i }).click();

  await page.getByRole('button', { name: /Finalizar|Finish|Concluir/i }).click();
  await page.getByText(/Bem-vindo|Welcome|¡Bienvenido!/i).waitFor({ state: 'visible', timeout: 20000 });
  await page.getByRole('button', { name: /Ir para Dashboard|Go to Dashboard|Ir al Dashboard/i }).click();
  await expect(page).toHaveURL(/\/dashboard(?:\?.*)?$/);
}

export async function bootstrapRegisteredUser(page: Page, testInfo: TestInfo, profile: OnboardingProfile = {}) {
  const user = buildE2EUserCredentials(testInfo);
  await registerViaUi(page, user);
  await completeOnboardingViaUi(page, { ...profile, name: profile.name ?? user.name });
  return page;
}

export async function bootstrapFreshUser(page: Page, testInfo: TestInfo) {
  const user = buildE2EUserCredentials(testInfo, 'fresh');
  await registerViaUi(page, user);
  return page;
}

export async function loginDemoUserViaUi(page: Page) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: /Login/i }).click();
  await page.getByTestId('login-email').fill('demo@fityq.it');
  await page.getByTestId('login-password').fill('FityqDemo!2026');
  await page.getByRole('button', { name: /Entrar/i }).click();
  await page.waitForURL('**/dashboard', { timeout: 20000 });
}
