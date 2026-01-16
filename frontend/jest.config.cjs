module.exports = {
  preset: 'jest-preset-angular',
  setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
  moduleNameMapper: {
    'ngx-markdown': '<rootDir>/src/mocks/ngx-markdown.js'
  },
  transform: {
    '^.+\\.(ts|js|html)$': ['jest-preset-angular', {
      tsconfig: '<rootDir>/tsconfig.spec.json',
      stringifyContentPathRegex: '\\.html$',
    }],
  },
  transformIgnorePatterns: ['node_modules/(?!(.*\\.mjs$|lodash-es|ng2-charts|chart.js))'],
};
