import { expect, type Page, type TestInfo } from '@playwright/test';

import { verifyEmailViaEmulator } from './firebase-emulator';

const apiBaseUrl = process.env.E2E_API_BASE_URL ?? 'http://localhost:8000';

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

  const uniqueSeed = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const email = `e2e-${slug}-${testInfo.repeatEachIndex}-${uniqueSeed}-${suffix}@fityq.it`;
  const name = `E2E ${slug.slice(0, 18)}`.trim();

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
  await expect(page).toHaveURL(/\/login(?:\?.*)?$/, { timeout: 20000 });
}

export async function loginViaUi(page: Page, user: E2EUserCredentials) {
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: /^Login$/i }).click();
  await page.getByTestId('login-email').fill(user.email);
  await page.getByTestId('login-password').fill(user.password);
  await page.getByRole('button', { name: /^Entrar$/i }).click();
}

export async function registerAndVerifyViaEmulator(page: Page, user: E2EUserCredentials) {
  await registerViaUi(page, user);
  await verifyEmailViaEmulator(page.request, user.email);
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
  const response = await page.request.post(`${apiBaseUrl}/user/e2e-login`, {
    data: {
      email: user.email,
      display_name: user.name,
      onboarding_completed: false,
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json() as { token?: string };
  expect(payload.token).toBeTruthy();
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.evaluate((token: string) => {
    localStorage.setItem('auth_token', token);
  }, payload.token!);
  await page.goto('/onboarding', { waitUntil: 'networkidle' });
  await completeOnboardingViaUi(page, { ...profile, name: profile.name ?? user.name });
  return page;
}

export async function bootstrapFreshUser(page: Page, testInfo: TestInfo) {
  const user = buildE2EUserCredentials(testInfo, 'fresh');
  const response = await page.request.post(`${apiBaseUrl}/user/e2e-login`, {
    data: {
      email: user.email,
      display_name: user.name,
      onboarding_completed: false,
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json() as { token?: string };
  expect(payload.token).toBeTruthy();
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.evaluate((token: string) => {
    localStorage.setItem('auth_token', token);
  }, payload.token!);
  await page.goto('/onboarding', { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/onboarding(?:\?.*)?$/, { timeout: 20000 });
  await expect(page.getByText(/Your Profile|Seu Perfil|Tu perfil/i)).toBeVisible({ timeout: 20000 });
  return page;
}

export async function loginDemoUserViaUi(page: Page) {
  const response = await page.request.post(`${apiBaseUrl}/user/e2e-login`, {
    data: {
      email: 'demo@fityq.it',
      display_name: 'Ethan Parker',
      onboarding_completed: true,
      is_demo: true,
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = await response.json() as { token?: string };
  expect(payload.token).toBeTruthy();

  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.evaluate((token: string) => {
    localStorage.setItem('auth_token', token);
  }, payload.token!);
  await page.goto('/dashboard', { waitUntil: 'networkidle' });
  await page.waitForURL('**/dashboard', { timeout: 20000 });
}
