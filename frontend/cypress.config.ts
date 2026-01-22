import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    defaultCommandTimeout: 15000,
    pageLoadTimeout: 60000,
    retries: {
      runMode: 1,
      openMode: 0
    },
    experimentalRetryOnNetworkFailure: false,
    setupNodeEvents(on) {
      on('task', {
        log(message) {
          console.warn(message);
          return null;
        },
      });
      // implement node event listeners here
    },
  },
});
