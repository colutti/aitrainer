import { expect, type APIRequestContext } from '@playwright/test';

const emulatorBaseUrl = process.env.E2E_FIREBASE_AUTH_EMULATOR_URL ?? 'http://localhost:9099';
const firebaseProjectId = process.env.E2E_FIREBASE_PROJECT_ID ?? 'demo-fityq';
const firebaseApiKey = process.env.E2E_FIREBASE_API_KEY ?? 'demo-api-key';

type OobRequestType = 'VERIFY_EMAIL' | 'PASSWORD_RESET';

interface OobCodeEntry {
  email: string;
  oobCode: string;
  requestType: OobRequestType;
}

async function listOobCodes(request: APIRequestContext): Promise<OobCodeEntry[]> {
  const response = await request.get(
    `${emulatorBaseUrl}/emulator/v1/projects/${firebaseProjectId}/oobCodes`
  );
  expect(response.ok()).toBeTruthy();

  const payload = (await response.json()) as { oobCodes?: OobCodeEntry[] };
  return payload.oobCodes ?? [];
}

async function waitForOobCode(
  request: APIRequestContext,
  email: string,
  requestType: OobRequestType
): Promise<string> {
  const normalizedEmail = email.trim().toLowerCase();

  for (let attempt = 0; attempt < 20; attempt += 1) {
    const codes = await listOobCodes(request);
    const match = [...codes]
      .reverse()
      .find((entry) => entry.email.trim().toLowerCase() === normalizedEmail && entry.requestType === requestType);

    if (match?.oobCode) {
      return match.oobCode;
    }

    await new Promise((resolve) => {
      setTimeout(resolve, 300);
    });
  }

  throw new Error(`Timed out waiting for ${requestType} oobCode for ${email}`);
}

export async function verifyEmailViaEmulator(
  request: APIRequestContext,
  email: string
): Promise<void> {
  const oobCode = await waitForOobCode(request, email, 'VERIFY_EMAIL');
  const response = await request.post(
    `${emulatorBaseUrl}/identitytoolkit.googleapis.com/v1/accounts:update`,
    {
      params: { key: firebaseApiKey },
      data: { oobCode },
    }
  );

  expect(response.ok()).toBeTruthy();
}

export async function resetPasswordViaEmulator(
  request: APIRequestContext,
  email: string,
  newPassword: string
): Promise<void> {
  const oobCode = await waitForOobCode(request, email, 'PASSWORD_RESET');
  const response = await request.post(
    `${emulatorBaseUrl}/identitytoolkit.googleapis.com/v1/accounts:resetPassword`,
    {
      params: { key: firebaseApiKey },
      data: {
        oobCode,
        newPassword,
      },
    }
  );

  expect(response.ok()).toBeTruthy();
}
