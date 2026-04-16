import { zodResolver } from '@hookform/resolvers/zod';
import { motion } from 'framer-motion';
import { Mail, Lock, LogIn, AlertCircle } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { PremiumCard } from '../../shared/components/ui/premium/PremiumCard';
import { useAuthStore } from '../../shared/hooks/useAuth';
import { usePublicConfig } from '../../shared/hooks/usePublicConfig';

const loginSchema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(6, 'A senha deve ter pelo menos 6 caracteres'),
});
const forgotPasswordEmailSchema = z.string().email();

const registerSchema = z.object({
  name: z.string().min(2, 'Nome deve ter pelo menos 2 caracteres'),
  email: z.string().email('E-mail inválido'),
  password: z.string().min(6, 'A senha deve ter pelo menos 6 caracteres'),
  confirmPassword: z.string().min(6, 'A confirmação deve ter pelo menos 6 caracteres'),
}).refine((data) => data.password === data.confirmPassword, {
  message: "As senhas não coincidem",
  path: ["confirmPassword"],
});

type LoginForm = z.infer<typeof loginSchema>;
type RegisterForm = z.infer<typeof registerSchema>;
type AuthLoadingAction = 'login' | 'register' | 'google' | 'forgot-password' | null;

export default function LoginPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const register = useAuthStore((state) => state.register);
  const socialLogin = useAuthStore((state) => state.socialLogin);
  const requestPasswordReset = useAuthStore((state) => state.requestPasswordReset);
  const { enableNewUserSignups } = usePublicConfig();
  const requestedRegisterMode = new URLSearchParams(location.search).get('mode') === 'register';
  const [isLogin, setIsLogin] = useState(!(requestedRegisterMode && enableNewUserSignups));
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<AuthLoadingAction>(null);

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/dashboard';

  const { register: registerLogin, handleSubmit: handleSubmitLogin, watch: watchLogin, formState: { errors: loginErrors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const { register: registerSignup, handleSubmit: handleSubmitSignup, formState: { errors: signupErrors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const resolveLoginErrorMessage = (err: unknown): string => {
    const authErrorCode = (
      typeof err === 'object' &&
      err !== null &&
      'code' in err &&
      typeof (err as { code?: unknown }).code === 'string'
    )
      ? (err as { code: string }).code
      : undefined;
    const authErrorMessage = err instanceof Error ? err.message : undefined;

    if (authErrorCode === 'auth/email-not-verified') {
      return t('auth.email_not_verified_error');
    }
    if (authErrorMessage?.toLowerCase().includes('verify your email')) {
      return t('auth.email_not_verified_error');
    }
    if (authErrorMessage?.toLowerCase().includes('new_signups_disabled')) {
      return t('auth.new_signups_disabled');
    }
    return t('auth.login_error');
  };

  const resolveRegisterErrorMessage = (err: unknown): string => {
    const authErrorCode = (
      typeof err === 'object' &&
      err !== null &&
      'code' in err &&
      typeof (err as { code?: unknown }).code === 'string'
    )
      ? (err as { code: string }).code
      : undefined;
    if (authErrorCode === 'auth/email-already-in-use') {
      return t('auth.user_exists_error');
    }
    if (authErrorCode === 'auth/new-signups-disabled') {
      return t('auth.new_signups_disabled');
    }
    return t('auth.login_error');
  };

  const onSubmitLogin = async (data: LoginForm) => {
    setLoadingAction('login');
    setError(null);
    setNotice(null);
    try {
      await login(data.email, data.password);
      void navigate(from, { replace: true });
    } catch (err) {
      setError(resolveLoginErrorMessage(err));
    } finally {
      setLoadingAction(null);
    }
  };

  const onSubmitSignup = async (data: RegisterForm) => {
    if (!enableNewUserSignups) {
      setError(t('auth.new_signups_disabled'));
      setNotice(null);
      return;
    }

    setLoadingAction('register');
    setError(null);
    setNotice(null);
    try {
      await register(data.name, data.email, data.password);
      setIsLogin(true);
      setNotice(t('auth.verify_email_sent'));
    } catch (err) {
      setError(resolveRegisterErrorMessage(err));
    } finally {
      setLoadingAction(null);
    }
  };

  const handleForgotPassword = async () => {
    const email = watchLogin('email').trim();
    if (!forgotPasswordEmailSchema.safeParse(email).success) {
      setError(t('auth.forgot_password_requires_email'));
      setNotice(null);
      return;
    }

    setLoadingAction('forgot-password');
    setError(null);
    setNotice(null);
    try {
      await requestPasswordReset(email, i18n.resolvedLanguage ?? i18n.language);
      setNotice(t('auth.forgot_password_sent_generic'));
    } catch (err) {
      const authErrorCode = (
        typeof err === 'object' &&
        err !== null &&
        'code' in err &&
        typeof (err as { code?: unknown }).code === 'string'
      )
        ? (err as { code: string }).code
        : undefined;

      if (authErrorCode === 'auth/user-not-found' || authErrorCode === 'auth/invalid-email') {
        // Keep generic feedback for account-enumeration-sensitive cases.
        setNotice(t('auth.forgot_password_sent_generic'));
      } else {
        setError(t('auth.forgot_password_send_error'));
      }
    } finally {
      setLoadingAction(null);
    }
  };

  const handleGoogleLogin = async () => {
    setLoadingAction('google');
    setError(null);
    setNotice(null);
    try {
      await socialLogin('google');
      void navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof Error && err.message.toLowerCase().includes('new_signups_disabled')) {
        setError(t('auth.new_signups_disabled'));
      } else {
        setError(t('auth.social_error'));
      }
    } finally {
      setLoadingAction(null);
    }
  };

  const isLoading = loadingAction !== null;
  const isEmailLoginLoading = loadingAction === 'login';
  const isGoogleLoginLoading = loadingAction === 'google';
  const isRegisterLoading = loadingAction === 'register';

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-4 selection:bg-white/20 overflow-hidden relative">
      {/* BACKGROUND DECORATION */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-orange-500/10 rounded-full blur-[120px]" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative z-10"
      >
        <div className="text-center mb-10">
          <h1 className="text-5xl font-black text-white tracking-tighter mb-2">FITYQ</h1>
          <p className="text-zinc-500 font-bold uppercase text-[10px] tracking-[0.3em]">{t('nav.brand_tagline')}</p>
        </div>

        <PremiumCard className="p-10 border-white/10 shadow-2xl backdrop-blur-3xl overflow-visible">
          {/* TABS */}
          <div className="flex bg-zinc-900/80 p-1.5 rounded-2xl mb-8 border border-zinc-700/60 relative">
            <div 
              data-testid="auth-tab-indicator"
              className="absolute h-[calc(100%-12px)] bg-zinc-800 rounded-xl shadow-[0_0_0_1px_rgba(45,212,191,0.35)] transition-all duration-500 ease-out"
              style={{ 
                width: enableNewUserSignups ? 'calc(50% - 6px)' : 'calc(100% - 12px)',
                left: isLogin ? '6px' : 'calc(50%)',
                transform: isLogin ? 'none' : 'translateX(0)'
              }}
            />
            <Button
              type="button"
              variant="ghost"
              onClick={() => { setIsLogin(true); }}
              className={`flex-1 h-auto py-3 text-[10px] font-black uppercase tracking-widest relative z-10 transition-colors duration-300 rounded-xl ${isLogin ? 'text-teal-300 hover:text-teal-200 hover:bg-transparent' : 'text-zinc-500 hover:text-zinc-300 hover:bg-transparent'}`}
            >
              Login
            </Button>
            {enableNewUserSignups && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => { setIsLogin(false); }}
                className={`flex-1 h-auto py-3 text-[10px] font-black uppercase tracking-widest relative z-10 transition-colors duration-300 rounded-xl ${!isLogin ? 'text-teal-300 hover:text-teal-200 hover:bg-transparent' : 'text-zinc-500 hover:text-zinc-300 hover:bg-transparent'}`}
              >
                Registro
              </Button>
            )}
          </div>
          {!enableNewUserSignups && (
            <p className="text-[10px] font-bold uppercase tracking-widest text-amber-300/80 mb-6 text-center">
              {t('auth.new_signups_disabled')}
            </p>
          )}

          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-2xl mb-6 flex items-center gap-3"
            >
              <AlertCircle size={18} />
              <p className="text-xs font-bold">{error}</p>
            </motion.div>
          )}
          {notice && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 p-4 rounded-2xl mb-6 flex items-center gap-3"
            >
              <AlertCircle size={18} />
              <p className="text-xs font-bold">{notice}</p>
            </motion.div>
          )}

          {isLogin ? (
            <form onSubmit={(e) => { void handleSubmitLogin(onSubmitLogin)(e); }} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">E-mail</label>
                <div className="relative">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600" size={18} />
                  <Input 
                    type="email" 
                    {...registerLogin('email')} 
                    data-testid="login-email"
                    error={loginErrors.email?.message}
                    placeholder="exemplo@email.com"
                    className="pl-12 h-14 rounded-2xl text-sm font-bold"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center px-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Senha</label>
                  <Button
                    type="button"
                    variant="ghost"
                    disabled={isLoading}
                    size="sm"
                    onClick={() => { void handleForgotPassword(); }}
                    className="h-auto p-0 text-[9px] font-black uppercase text-indigo-400 hover:text-indigo-300 transition-colors hover:bg-transparent"
                  >
                    {t('auth.forgot_password')}
                  </Button>
                </div>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600" size={18} />
                  <Input 
                    type="password" 
                    {...registerLogin('password')} 
                    data-testid="login-password"
                    error={loginErrors.password?.message}
                    placeholder="••••••••"
                    className="pl-12 h-14 rounded-2xl text-sm font-bold"
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                fullWidth 
                size="lg" 
                isLoading={isEmailLoginLoading}
                disabled={isLoading && !isEmailLoginLoading}
                className="h-14 rounded-2xl bg-[#14b8a6] text-black border border-[#2dd4bf]/30 shadow-none hover:bg-[#0d9488] hover:scale-[1.02] active:scale-[0.98] transition-all mt-4"
              >
                <LogIn className="mr-2 w-5 h-5" />
                Entrar
              </Button>

              <div className="grid grid-cols-1 gap-3 pt-2">
                <Button
                  type="button"
                  fullWidth
                  size="lg"
                  isLoading={isGoogleLoginLoading}
                  disabled={isLoading && !isGoogleLoginLoading}
                  onClick={() => { void handleGoogleLogin(); }}
                  className="h-14 rounded-2xl bg-white text-[#1f1f1f] border border-[#747775] hover:bg-[#f8fafd] hover:border-[#5f6368] font-medium shadow-none transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1a73e8]/30"
                >
                  <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                    <path fill="#4285F4" d="M23.49 12.27c0-.79-.07-1.54-.2-2.27H12v4.3h6.44a5.5 5.5 0 0 1-2.39 3.6v2.98h3.86c2.26-2.08 3.58-5.14 3.58-8.61Z" />
                    <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.92l-3.86-2.98c-1.08.72-2.45 1.14-4.07 1.14-3.13 0-5.78-2.12-6.72-4.98H1.3v3.07A12 12 0 0 0 12 24Z" />
                    <path fill="#FBBC05" d="M5.28 14.26A7.2 7.2 0 0 1 4.9 12c0-.78.14-1.53.38-2.26V6.67H1.3A12 12 0 0 0 0 12c0 1.94.46 3.78 1.3 5.33l3.98-3.07Z" />
                    <path fill="#EA4335" d="M12 4.77c1.76 0 3.33.6 4.57 1.8l3.42-3.42C17.94 1.22 15.24 0 12 0A12 12 0 0 0 1.3 6.67l3.98 3.07C6.22 6.9 8.87 4.77 12 4.77Z" />
                  </svg>
                  {t('auth.google_sign_in')}
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={(e) => { void handleSubmitSignup(onSubmitSignup)(e); }} className="space-y-5">
              <div className="space-y-1.5">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Nome Completo</label>
                <Input 
                  {...registerSignup('name')} 
                  data-testid="register-name"
                  error={signupErrors.name?.message}
                  placeholder="Seu nome"
                  className="h-14 rounded-2xl text-sm font-bold"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">E-mail</label>
                <Input 
                  type="email" 
                  {...registerSignup('email')} 
                  data-testid="register-email"
                  error={signupErrors.email?.message}
                  placeholder="exemplo@email.com"
                  className="h-14 rounded-2xl text-sm font-bold"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Senha</label>
                  <Input 
                    type="password" 
                    {...registerSignup('password')} 
                    data-testid="register-password"
                    error={signupErrors.password?.message}
                    className="h-14 rounded-2xl text-sm font-bold"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Confirmar</label>
                  <Input 
                    type="password" 
                    {...registerSignup('confirmPassword')} 
                    data-testid="register-confirm-password"
                    error={signupErrors.confirmPassword?.message}
                    className="h-14 rounded-2xl text-sm font-bold"
                  />
                </div>
              </div>
              <Button 
                type="submit" 
                fullWidth 
                size="lg" 
                isLoading={isRegisterLoading}
                disabled={isLoading && !isRegisterLoading}
                className="h-14 rounded-2xl bg-[#14b8a6] text-black border border-[#2dd4bf]/30 shadow-none hover:bg-[#0d9488] hover:scale-[1.02] active:scale-[0.98] transition-all mt-4"
              >
                Criar Conta
              </Button>
            </form>
          )}
        </PremiumCard>

        <p className="text-center mt-10 text-[10px] font-bold text-zinc-600 uppercase tracking-widest leading-loose">
          Ao continuar, você aceita nossos <Link to="/termos-de-uso" className="text-zinc-400 hover:text-white transition-colors">Termos de Uso</Link> e <Link to="/politica-de-privacidade" className="text-zinc-400 hover:text-white transition-colors">Política de Privacidade</Link>
        </p>
      </motion.div>
    </div>
  );
}
