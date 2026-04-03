import { initializeApp } from 'firebase/app';
import { connectAuthEmulator, getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY as string,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID as string,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET as string,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID as string,
  appId: import.meta.env.VITE_FIREBASE_APP_ID as string,
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);

const useAuthEmulator = import.meta.env.VITE_USE_FIREBASE_AUTH_EMULATOR === 'true';
const authEmulatorUrl = import.meta.env.VITE_FIREBASE_AUTH_EMULATOR_URL as string | undefined;

if (useAuthEmulator && authEmulatorUrl) {
  connectAuthEmulator(auth, authEmulatorUrl, { disableWarnings: true });
}
