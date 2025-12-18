import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
    eslint.configs.recommended,
    ...tseslint.configs.recommended,
    {
        files: ['**/*.ts'],
        rules: {
            '@typescript-eslint/no-unused-vars': 'warn',
            '@typescript-eslint/no-explicit-any': 'warn',
            '@typescript-eslint/explicit-function-return-type': 'off',
            'no-console': ['warn', { allow: ['error', 'warn'] }],
        },
    },
    {
        ignores: ['node_modules/', 'dist/', '.angular/', 'cypress/'],
    }
);
