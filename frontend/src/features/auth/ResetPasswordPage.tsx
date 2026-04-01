import { zodResolver } from '@hookform/resolvers/zod';
import { AlertCircle, CheckCircle2, Lock } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { PremiumCard } from '../../shared/components/ui/premium/PremiumCard';

const resetPasswordSchema = z.object({
  password: z.string()
    .min(8, 'A senha deve ter no mínimo 8 caracteres')
    .regex(/[A-Z]/, 'A senha deve ter ao menos 1 letra maiúscula')
    .regex(/[a-z]/, 'A senha deve ter ao menos 1 letra minúscula')
    .regex(/[0-9]/, 'A senha deve ter ao menos 1 número'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  path: ['confirmPassword'],
  message: 'As senhas não coincidem',
});

type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCodeValid, setIsCodeValid] = useState<boolean | null>(null);
  const [isResetDone, setIsResetDone] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const oobCode = useMemo(() => searchParams.get('oobCode') ?? '', [searchParams]);

  const { register, handleSubmit, formState: { errors } } = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
  });

  useEffect(() => {
    if (!oobCode) {
      setIsCodeValid(false);
      return;
    }

    void (async () => {
      try {
        const { auth } = await import('./firebase');
        const { verifyPasswordResetCode } = await import('firebase/auth');
        await verifyPasswordResetCode(auth, oobCode);
        setIsCodeValid(true);
      } catch {
        setIsCodeValid(false);
      }
    })();
  }, [oobCode]);

  const onSubmit = async (data: ResetPasswordForm) => {
    if (!oobCode) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const { auth } = await import('./firebase');
      const { confirmPasswordReset } = await import('firebase/auth');
      await confirmPasswordReset(auth, oobCode, data.password);
      setIsResetDone(true);
    } catch {
      setErrorMessage('Não foi possível redefinir a senha. Tente novamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <PremiumCard className="p-8 border-white/10 shadow-2xl backdrop-blur-3xl">
          <h1 className="text-2xl font-black text-white tracking-tight mb-2">Redefinir senha</h1>
          <p className="text-zinc-400 text-sm mb-6">Defina uma nova senha para sua conta.</p>

          {isCodeValid === false && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-2xl flex items-center gap-3">
              <AlertCircle size={18} />
              <p className="text-xs font-bold">Link inválido ou expirado.</p>
            </div>
          )}

          {isCodeValid === null && (
            <p className="text-xs font-bold text-zinc-400">Validando link...</p>
          )}

          {isCodeValid === true && !isResetDone && (
            <form onSubmit={(e) => { void handleSubmit(onSubmit)(e); }} className="space-y-4">
              <div>
                <label htmlFor="password" className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-1 block">
                  Nova senha
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  leftIcon={<Lock size={16} />}
                  error={errors.password?.message}
                  {...register('password')}
                />
              </div>

              <div>
                <label htmlFor="confirmPassword" className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-1 block">
                  Confirmar nova senha
                </label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="••••••••"
                  leftIcon={<Lock size={16} />}
                  error={errors.confirmPassword?.message}
                  {...register('confirmPassword')}
                />
              </div>

              {errorMessage && (
                <p className="text-xs font-bold text-red-400">{errorMessage}</p>
              )}

              <Button type="submit" fullWidth isLoading={isSubmitting}>
                Redefinir senha
              </Button>
            </form>
          )}

          {isResetDone && (
            <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 p-4 rounded-2xl flex items-center gap-3">
              <CheckCircle2 size={18} />
              <p className="text-xs font-bold">
                Senha redefinida com sucesso. <Link to="/login" className="underline">Entrar agora</Link>
              </p>
            </div>
          )}
        </PremiumCard>
      </div>
    </div>
  );
}
