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

const loginSchema = z.object({
  email: z.string().email('E-mail inválido'),
  password: z.string().min(6, 'A senha deve ter pelo menos 6 caracteres'),
});

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

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((state) => state.login);
  const register = useAuthStore((state) => state.register);
  const initialMode = new URLSearchParams(location.search).get('mode') === 'register' ? 'register' : 'login';
  const [isLogin, setIsLogin] = useState(initialMode === 'login');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? '/dashboard';

  const { register: registerLogin, handleSubmit: handleSubmitLogin, formState: { errors: loginErrors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const { register: registerSignup, handleSubmit: handleSubmitSignup, formState: { errors: signupErrors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmitLogin = async (data: LoginForm) => {
    setIsLoading(true);
    setError(null);
    try {
      await login(data.email, data.password);
      void navigate(from, { replace: true });
    } catch {
      setError(t('auth.login_error'));
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmitSignup = async (data: RegisterForm) => {
    setIsLoading(true);
    setError(null);
    try {
      await register(data.name, data.email, data.password);
      void navigate('/onboarding', { replace: true });
    } catch {
      setError(t('auth.login_error'));
    } finally {
      setIsLoading(false);
    }
  };

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
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6 backdrop-blur-xl shadow-inner">
            <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
            <span className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-400">Deep Space Premium</span>
          </div>
          <h1 className="text-5xl font-black text-white tracking-tighter mb-2">FITYQ</h1>
          <p className="text-zinc-500 font-bold uppercase text-[10px] tracking-[0.3em]">{t('nav.brand_tagline')}</p>
        </div>

        <PremiumCard className="p-10 border-white/10 shadow-2xl backdrop-blur-3xl overflow-visible">
          {/* TABS */}
          <div className="flex bg-white/5 p-1.5 rounded-2xl mb-8 border border-white/5 relative">
            <div 
              className="absolute h-[calc(100%-12px)] bg-white rounded-xl shadow-lg transition-all duration-500 ease-out"
              style={{ 
                width: 'calc(50% - 6px)', 
                left: isLogin ? '6px' : 'calc(50%)',
                transform: isLogin ? 'none' : 'translateX(0)'
              }}
            />
            <button
              onClick={() => { setIsLogin(true); }}
              className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest relative z-10 transition-colors duration-300 ${isLogin ? 'text-black' : 'text-zinc-500'}`}
            >
              Login
            </button>
            <button
              onClick={() => { setIsLogin(false); }}
              className={`flex-1 py-3 text-[10px] font-black uppercase tracking-widest relative z-10 transition-colors duration-300 ${!isLogin ? 'text-black' : 'text-zinc-500'}`}
            >
              Registro
            </button>
          </div>

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
                    className="pl-12 h-14 bg-white/5 border-white/5 focus:border-white/20 rounded-2xl text-sm font-bold text-white"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center px-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Senha</label>
                  <button type="button" className="text-[9px] font-black uppercase text-indigo-400 hover:text-indigo-300 transition-colors">Esqueci a senha</button>
                </div>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600" size={18} />
                  <Input 
                    type="password" 
                    {...registerLogin('password')} 
                    data-testid="login-password"
                    error={loginErrors.password?.message}
                    placeholder="••••••••"
                    className="pl-12 h-14 bg-white/5 border-white/5 focus:border-white/20 rounded-2xl text-sm font-bold text-white"
                  />
                </div>
              </div>

              <Button 
                type="submit" 
                fullWidth 
                size="lg" 
                isLoading={isLoading}
                className="h-14 rounded-2xl bg-white text-black font-black shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all mt-4"
              >
                <LogIn className="mr-2 w-5 h-5" />
                Entrar
              </Button>
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
                  className="h-14 bg-white/5 border-white/5 focus:border-white/20 rounded-2xl text-sm font-bold text-white"
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
                  className="h-14 bg-white/5 border-white/5 focus:border-white/20 rounded-2xl text-sm font-bold text-white"
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
                    className="h-14 bg-white/5 border-white/5 focus:border-white/20 rounded-2xl text-sm font-bold text-white"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Confirmar</label>
                  <Input 
                    type="password" 
                    {...registerSignup('confirmPassword')} 
                    data-testid="register-confirm-password"
                    error={signupErrors.confirmPassword?.message}
                    className="h-14 bg-white/5 border-white/5 focus:border-white/20 rounded-2xl text-sm font-bold text-white"
                  />
                </div>
              </div>
              <Button 
                type="submit" 
                fullWidth 
                size="lg" 
                isLoading={isLoading}
                className="h-14 rounded-2xl bg-white text-black font-black shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all mt-4"
              >
                Criar Conta
              </Button>
            </form>
          )}
        </PremiumCard>

        <p className="text-center mt-10 text-[10px] font-bold text-zinc-600 uppercase tracking-widest leading-loose">
          Ao continuar, você aceita nossos <Link to="/terms" className="text-zinc-400 hover:text-white transition-colors">Termos de Uso</Link> e <Link to="/privacy" className="text-zinc-400 hover:text-white transition-colors">Privacidade</Link>
        </p>
      </motion.div>
    </div>
  );
}
