export interface AppRuntimeConfig {
  VITE_API_URL?: string;
  VITE_FIREBASE_API_KEY?: string;
  VITE_FIREBASE_AUTH_DOMAIN?: string;
  VITE_FIREBASE_PROJECT_ID?: string;
  VITE_FIREBASE_STORAGE_BUCKET?: string;
  VITE_FIREBASE_MESSAGING_SENDER_ID?: string;
  VITE_FIREBASE_APP_ID?: string;
  VITE_USE_FIREBASE_AUTH_EMULATOR?: string;
  VITE_FIREBASE_AUTH_EMULATOR_URL?: string;
}

declare global {
  interface Window {
    __APP_CONFIG__?: AppRuntimeConfig;
  }
}

export const getRuntimeConfig = (): AppRuntimeConfig => {
  if (typeof window === 'undefined') {
    return {};
  }

  return window.__APP_CONFIG__ ?? {};
};

export const getRuntimeConfigValue = (key: keyof AppRuntimeConfig): string | undefined => {
  const value = getRuntimeConfig()[key];
  if (typeof value !== 'string' || value.trim().length === 0) {
    return undefined;
  }
  return value;
};
