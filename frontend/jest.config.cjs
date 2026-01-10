module.exports = {
  preset: 'jest-preset-angular',
  setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/'
  ],
  transform: {
    '^.+\\.(ts|js|html)$': ['jest-preset-angular', {
        tsconfig: '<rootDir>/src/tsconfig.spec.json',
        stringifyContentPathRegex: '\\.(html|svg)$',
    }] 
  },
  transformIgnorePatterns: ['node_modules/(?!(@angular|.*\\.mjs$|lodash-es|ng2-charts|chart.js)/)']
};
