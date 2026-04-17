import { initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';
import type { Auth } from 'firebase/auth';

import { getRuntimeConfigValue } from '../../shared/config/runtime-config';

const firebaseConfig = {
  apiKey: getRuntimeConfigValue('VITE_FIREBASE_API_KEY') ?? (import.meta.env.VITE_FIREBASE_API_KEY as string | undefined),
  authDomain: getRuntimeConfigValue('VITE_FIREBASE_AUTH_DOMAIN') ?? (import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string | undefined),
  projectId: getRuntimeConfigValue('VITE_FIREBASE_PROJECT_ID') ?? (import.meta.env.VITE_FIREBASE_PROJECT_ID as string | undefined),
  storageBucket: getRuntimeConfigValue('VITE_FIREBASE_STORAGE_BUCKET') ?? (import.meta.env.VITE_FIREBASE_STORAGE_BUCKET as string | undefined),
  messagingSenderId: getRuntimeConfigValue('VITE_FIREBASE_MESSAGING_SENDER_ID') ?? (import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID as string | undefined),
  appId: getRuntimeConfigValue('VITE_FIREBASE_APP_ID') ?? (import.meta.env.VITE_FIREBASE_APP_ID as string | undefined),
};

const useAuthEmulator =
  (getRuntimeConfigValue('VITE_USE_FIREBASE_AUTH_EMULATOR') ?? (import.meta.env.VITE_USE_FIREBASE_AUTH_EMULATOR as string | undefined)) === 'true';
const authEmulatorUrl =
  getRuntimeConfigValue('VITE_FIREBASE_AUTH_EMULATOR_URL') ?? (import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_URL as string | undefined);
let authInstance: Auth | null = null;

const hasRequiredFirebaseConfig = () =>
  Object.values(firebaseConfig).every((value) => typeof value === 'string' && value.trim().length > 0);

export const getFirebaseAuth = (): Auth => {
  if (authInstance) {
    return authInstance;
  }

  if (!hasRequiredFirebaseConfig()) {
    throw new Error('Firebase auth is not configured');
  }

  const app = initializeApp(firebaseConfig);
  authInstance = getAuth(app);

  if (useAuthEmulator && authEmulatorUrl) {
    connectAuthEmulator(authInstance, authEmulatorUrl, { disableWarnings: true });
  }

  return authInstance;
};
