import { loadRuntimeConfig } from './bootstrap-runtime';

const bootstrapApp = async () => {
  await loadRuntimeConfig();
  await import('./main');
};

void bootstrapApp();
