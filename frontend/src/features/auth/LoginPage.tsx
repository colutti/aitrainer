import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, Lock, LogIn } from 'lucide-react';
import { useState, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { LanguageSelector } from '../../shared/components/ui/LanguageSelector';
import { useAuthStore } from '../../shared/hooks/useAuth';
import { useNotificationStore } from '../../shared/hooks/useNotification';

/**
 * LoginPage component
 * 
 * Provides a premium login experience with validation and error handling.
 */
export function LoginPage() {
  const { t } = useTranslation();
  const [isLoading, setIsLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
  const socialLogin = useAuthStore((state) => state.socialLogin);
  const notify = useNotificationStore();
  const navigate = useNavigate();

  // Validation schema defined inside to allow for dynamic translations
  const loginSchema = useMemo(() => z.object({
    email: z.string().email(t('validation.email_invalid')),
    password: z.string().min(6, t('validation.password_min')),
  }), [t]);

  type LoginForm = z.infer<typeof loginSchema>;

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(false); // Reset just in case, but usually handled by isSubmitting
    try {
      await login(data.email, data.password);
      notify.success(t('login.welcome_back'));
      await navigate('/');
    } catch (error: unknown) {
      console.error('Login error:', error);
      const errorCode = error instanceof Error && 'code' in error 
        ? (error as { code: string }).code 
        : '';
      const message = errorCode === 'auth/invalid-credential' 
        ? t('login.invalid_credentials') 
        : t('login.error_message');
      notify.error(message);
    }
  };

  const handleForgotPassword = async () => {
    const email = getValues('email');
    if (!email) {
      notify.error(t('login.enter_email_first'));
      return;
    }
    
    try {
      const { auth } = await import('../../features/auth/firebase');
      const { sendPasswordResetEmail } = await import('firebase/auth');
      await sendPasswordResetEmail(auth, email);
      notify.success(t('login.password_reset_sent'));
    } catch (error: unknown) {
      console.error('Password reset error:', error);
      notify.error(t('login.error_message'));
    }
  };

  return (
    <div className="min-h-screen w-full flex bg-dark-bg overflow-hidden font-outfit">
      {/* Left Side: Visual Experience */}
      <div className="hidden lg:flex lg:w-3/5 relative overflow-hidden group">
        <img 
          src="/login_side.png" 
          alt="Professional Fitness Experience" 
          className="absolute inset-0 w-full h-full object-cover transition-transform duration-[10s] group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-linear-to-r from-dark-bg via-dark-bg/20 to-transparent" />
        <div className="absolute inset-0 bg-black/30 backdrop-blur-[2px]" />
        
        {/* Brand Overlay */}
        <div className="absolute top-12 left-12 animate-in fade-in slide-in-from-left duration-1000">
           <div className="flex items-center gap-4">
              <img src="/brand_icon_final.png" alt="FityQ" className="h-28 w-28 drop-shadow-2xl brightness-110" />
              <div>
                <h1 className="text-4xl font-black text-white tracking-widest uppercase">FityQ</h1>
                <p className="text-gradient-start font-bold uppercase tracking-[0.3em] text-xs">{t('login.brand_tagline')}</p>
              </div>
           </div>
        </div>

        <div className="absolute bottom-12 left-12 max-w-lg animate-in fade-in slide-in-from-bottom duration-1000 delay-300">
          <h2 className="text-5xl font-bold text-white leading-tight">
            {t('login.marketing_title').split('Performance').map((part, i) => (
              <span key={i}>
                {part}
                {i === 0 && <span className="text-gradient-start">Performance</span>}
              </span>
            ))}
          </h2>
          <p className="text-text-secondary mt-6 text-lg leading-relaxed">
            {t('login.marketing_subtitle')}
          </p>
        </div>
      </div>

      {/* Right Side: Login Form */}
      <div className="w-full lg:w-2/5 flex items-center justify-center p-8 bg-dark-bg relative z-10 border-l border-white/5 shadow-[-20px_0_50px_rgba(0,0,0,0.5)]">
        <div className="w-full max-w-md space-y-10 animate-in fade-in slide-in-from-right duration-700 bg-white/2 p-10 rounded-[2.5rem] border border-white/5 backdrop-blur-xl relative">
          <div className="absolute top-6 right-6 lg:top-8 lg:right-8">
            <LanguageSelector />
          </div>
          <div className="lg:hidden text-center mb-10">
            <img src="/brand_icon_final.png" alt="FityQ" className="h-36 w-auto mx-auto drop-shadow-2xl mb-4 brightness-110" />
            <h1 className="text-3xl font-bold text-white tracking-widest">FityQ</h1>
          </div>

          <div className="space-y-4">
            <h2 className="text-4xl font-extrabold text-white tracking-tight">{t('login.title')}</h2>
            <p className="text-text-secondary text-lg">{t('login.subtitle')}</p>
          </div>

          <form 
            onSubmit={(e) => {
              void handleSubmit(onSubmit)(e);
            }} 
            className="space-y-8"
          >
            <div className="space-y-4">
              <Input
                label={t('login.email_label')}
                id="email"
                type="email"
                placeholder={t('login.email_placeholder')}
                leftIcon={<Mail size={20} className="text-text-muted" />}
                className="bg-white/5 border-white/10 h-14"
                error={errors.email?.message}
                {...register('email')}
              />

              <Input
                label={t('login.password_label')}
                id="password"
                type="password"
                placeholder={t('login.password_placeholder')}
                leftIcon={<Lock size={20} className="text-text-muted" />}
                className="bg-white/5 border-white/10 h-14"
                error={errors.password?.message}
                {...register('password')}
              />
            </div>

            <div className="flex items-center justify-end">
              <button
                type="button"
                onClick={() => void handleForgotPassword()}
                className="text-sm font-semibold text-gradient-start hover:text-gradient-end transition-colors underline-offset-4 hover:underline"
              >
                {t('login.forgot_password')}
              </button>
            </div>

            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              className="h-14 text-xl font-bold bg-linear-to-r from-gradient-start to-gradient-end shadow-orange hover:shadow-orange/40 transition-all rounded-xl"
            >
              {t('login.submit')}
              {!isLoading && <LogIn className="ml-3" size={22} />}
            </Button>
          </form>

          <div className="relative flex items-center py-2">
            <div className="grow border-t border-white/10"></div>
            <span className="shrink-0 px-4 text-text-muted text-sm uppercase tracking-wider">
              {t('login.or_continue_with') || "Ou continue com"}
            </span>
            <div className="grow border-t border-white/10"></div>
          </div>

          <Button
            type="button"
            variant="secondary"
            fullWidth
            onClick={() => void socialLogin('google')}
            className="h-14 bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20 text-white font-semibold flex items-center justify-center gap-3 transition-colors rounded-xl"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Google
          </Button>
        </div>
      </div>
    </div>
  );
}
