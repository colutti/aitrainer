import { describe, expect, it } from 'vitest';

import { validateStrongPassword } from './password-policy';

describe('validateStrongPassword', () => {
  it('accepts a strong password', () => {
    const result = validateStrongPassword('FityQ!2026');
    expect(result.success).toBe(true);
  });

  it('rejects weak passwords and reports all unmet requirements', () => {
    const result = validateStrongPassword('abc');
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.errors).toEqual(expect.arrayContaining([
        'auth.password_rule_min_length',
        'auth.password_rule_uppercase',
        'auth.password_rule_number',
        'auth.password_rule_special',
      ]));
    }
  });
});
