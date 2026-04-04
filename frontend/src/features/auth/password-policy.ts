interface PasswordValidationSuccess {
  success: true;
  errors: [];
}

interface PasswordValidationFailure {
  success: false;
  errors: string[];
}

export type PasswordValidationResult = PasswordValidationSuccess | PasswordValidationFailure;

const PASSWORD_RULES: readonly { key: string; test: (value: string) => boolean }[] = [
  { key: 'auth.password_rule_min_length', test: (value) => value.length >= 8 },
  { key: 'auth.password_rule_uppercase', test: (value) => /[A-Z]/.test(value) },
  { key: 'auth.password_rule_lowercase', test: (value) => /[a-z]/.test(value) },
  { key: 'auth.password_rule_number', test: (value) => /\d/.test(value) },
  { key: 'auth.password_rule_special', test: (value) => /[^A-Za-z0-9]/.test(value) },
];

export function validateStrongPassword(password: string): PasswordValidationResult {
  const errors = PASSWORD_RULES
    .filter((rule) => !rule.test(password))
    .map((rule) => rule.key);

  if (errors.length > 0) {
    return { success: false, errors };
  }

  return { success: true, errors: [] };
}
