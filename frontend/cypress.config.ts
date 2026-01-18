import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    defaultCommandTimeout: 15000,
    pageLoadTimeout: 60000,
    retries: {
      runMode: 3,
      openMode: 0
    },
    experimentalRetryOnNetworkFailure: false,
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
