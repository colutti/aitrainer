import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    // Fail-fast configuration: reduzir timeouts agressivamente
    defaultCommandTimeout: 8000,      // 8s (era 15s)
    pageLoadTimeout: 25000,           // 25s (era 60s)
    requestTimeout: 8000,             // 8s para requisições
    responseTimeout: 8000,            // 8s para respostas

    // Política de fail-fast: sem retries automáticos
    retries: {
      runMode: 0,    // Sem retries em modo headless (era 1)
      openMode: 0    // Sem retries em modo interativo
    },

    // Desabilitar retry automático de falhas de rede
    experimentalRetryOnNetworkFailure: false,

    // Configurações de performance
    experimentalSlurpChanges: true,   // Melhor performance em modo headless
    numTestsKeptInMemory: 0,          // Liberar memória após cada teste

    // Configuração de viewport
    viewportWidth: 1280,
    viewportHeight: 720,

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

  // Suporte para paralelização (Cypress 13+)
  // Usar: npx cypress run --parallel
  // ou: npm run cypress:parallel (definido em package.json)
  component: {
    devServer: {
      framework: 'angular',
      bundler: 'webpack',
    },
  },
});
