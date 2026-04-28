import { AlertCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { SyntheticEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { PremiumCard } from '../../shared/components/ui/premium/PremiumCard';

import { getFirebaseAuth } from './firebase';
import { validateStrongPassword } from './password-policy';

const parseNestedQueryParam = (searchParams: URLSearchParams, key: string): string => {
  const directValue = searchParams.get(key);
  if (directValue) {
    return directValue;
  }

  const nestedLink = searchParams.get('link');
  if (!nestedLink) {
    return '';
  }

  try {
    const nestedUrl = new URL(nestedLink);
    return nestedUrl.searchParams.get(key) ?? '';
  } catch {
    return '';
  }
};

export default function ResetPasswordPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isValidatingCode, setIsValidatingCode] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [passwordErrors, setPasswordErrors] = useState<string[]>([]);

  const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
  const mode = parseNestedQueryParam(searchParams, 'mode');
  const oobCode = parseNestedQueryParam(searchParams, 'oobCode');
  const isSupportedMode = mode === 'resetPassword';

  useEffect(() => {
    const validateCode = async () => {
      if (!isSupportedMode || !oobCode) {
        setErrorKey('auth.reset_link_invalid');
        setIsValidatingCode(false);
        return;
      }

      try {
        const { verifyPasswordResetCode } = await import('firebase/auth');
        const auth = getFirebaseAuth();
        await verifyPasswordResetCode(auth, oobCode);
      } catch {
        setErrorKey('auth.reset_link_invalid');
      } finally {
        setIsValidatingCode(false);
      }
    };

    void validateCode();
  }, [isSupportedMode, oobCode]);

  const handleSubmit = async (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validation = validateStrongPassword(newPassword);
    if (!validation.success) {
      setPasswordErrors(validation.errors);
      setErrorKey(null);
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordErrors([]);
      setErrorKey('auth.password_mismatch');
      return;
    }

    setIsSubmitting(true);
    setPasswordErrors([]);
    setErrorKey(null);
    try {
      const { confirmPasswordReset } = await import('firebase/auth');
      const auth = getFirebaseAuth();
      await confirmPasswordReset(auth, oobCode, newPassword);
      setIsSuccess(true);
    } catch {
      setErrorKey('auth.reset_password_error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      data-testid="auth-form-shell"
      className="min-h-screen bg-[color:var(--color-background)] text-[color:var(--color-on-background)] flex items-center justify-center p-4"
    >

      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-10">
          <h1 className="text-5xl font-semibold text-[color:var(--color-on-surface)] tracking-tighter mb-2">FITYQ</h1>
          <p className="text-[color:var(--color-on-surface-variant)] font-bold uppercase text-[10px] tracking-[0.3em]">{t('nav.brand_tagline')}</p>
        </div>

        <PremiumCard className="p-10 border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container-high)]">
          <h2 className="text-xl font-semibold text-[color:var(--color-on-surface)] uppercase tracking-[0.05em] mb-6">
            {t('auth.reset_password_title')}
          </h2>

          {isValidatingCode ? (
            <p className="text-sm text-zinc-300">{t('common.loading')}</p>
          ) : null}

          {!isValidatingCode && errorKey ? (
            <div className="bg-[color:var(--color-error)]/10 border border-[color:var(--color-error)]/20 text-[color:var(--color-error)] p-4 rounded-2xl mb-6 flex items-center gap-3">
              <AlertCircle size={18} />
              <p className="text-xs font-bold">{t(errorKey)}</p>
            </div>
          ) : null}

          {!isValidatingCode && !errorKey && !isSuccess ? (
            <form onSubmit={(event) => { void handleSubmit(event); }} className="space-y-5">
              <Input
                id="new-password"
                type="password"
                label={t('auth.new_password')}
                value={newPassword}
                onChange={(event) => { setNewPassword(event.target.value); }}
                placeholder="••••••••"
              />

              <Input
                id="confirm-password"
                type="password"
                label={t('auth.confirm_new_password')}
                value={confirmPassword}
                onChange={(event) => { setConfirmPassword(event.target.value); }}
                placeholder="••••••••"
              />

              {passwordErrors.length > 0 ? (
                <div className="bg-[color:var(--color-error)]/10 border border-[color:var(--color-error)]/20 text-red-300 p-4 rounded-2xl">
                  <ul className="list-disc ml-4 space-y-1 text-xs font-bold">
                    {passwordErrors.map((passwordError) => (
                      <li key={passwordError}>{t(passwordError)}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <Button
                type="submit"
                fullWidth
                size="lg"
                isLoading={isSubmitting}
                className="h-14 rounded-2xl"
              >
                {t('auth.save_new_password')}
              </Button>
            </form>
          ) : null}

          {!isValidatingCode && isSuccess ? (
            <div className="space-y-6">
              <div className="bg-[color:var(--color-secondary)]/10 border border-[color:var(--color-secondary)]/20 text-emerald-300 p-4 rounded-2xl flex items-center gap-3">
                <AlertCircle size={18} />
                <p className="text-xs font-bold">{t('auth.reset_password_success')}</p>
              </div>
              <Button
                type="button"
                fullWidth
                size="lg"
                className="h-14 rounded-2xl"
                onClick={() => { void navigate('/login'); }}
              >
                {t('common.back')}
              </Button>
            </div>
          ) : null}
        </PremiumCard>
      </div>
    </div>
  );
}
