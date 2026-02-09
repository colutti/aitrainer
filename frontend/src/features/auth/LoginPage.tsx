import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, Lock, LogIn } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { Button } from '../../shared/components/ui/Button';
import { Input } from '../../shared/components/ui/Input';
import { useAuthStore } from '../../shared/hooks/useAuth';
import { useNotificationStore } from '../../shared/hooks/useNotification';

// Validation schema
const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(6, 'A senha deve ter pelo menos 6 caracteres'),
});

type LoginForm = z.infer<typeof loginSchema>;

/**
 * LoginPage component
 * 
 * Provides a premium login experience with validation and error handling.
 */
export function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
  const notify = useNotificationStore();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    try {
      await login(data.email, data.password);
      notify.success('Bem-vindo de volta!');
      await navigate('/');
    } catch (error) {
      notify.error('Falha no login. Verifique suas credenciais.');
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
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
        <div className="absolute inset-0 bg-gradient-to-r from-dark-bg via-dark-bg/20 to-transparent" />
        <div className="absolute inset-0 bg-black/30 backdrop-blur-[2px]" />
        
        {/* Brand Overlay */}
        <div className="absolute top-12 left-12 animate-in fade-in slide-in-from-left duration-1000">
           <div className="flex items-center gap-4">
              <img src="/brand_icon_final.png" alt="FIT IQ" className="h-16 w-16 drop-shadow-2xl brightness-110" />
              <div>
                <h1 className="text-4xl font-black text-white tracking-widest uppercase">FIT IQ</h1>
                <p className="text-gradient-start font-bold uppercase tracking-[0.3em] text-xs">Intelligence x Fitness</p>
              </div>
           </div>
        </div>

        <div className="absolute bottom-12 left-12 max-w-lg animate-in fade-in slide-in-from-bottom duration-1000 delay-300">
          <h2 className="text-5xl font-bold text-white leading-tight">
            Eleve sua <span className="text-gradient-start">Performance</span> com Inteligência Artificial.
          </h2>
          <p className="text-text-secondary mt-6 text-lg leading-relaxed">
            Acompanhamento completo de dieta, treinos e metabolismo em uma única plataforma premium.
          </p>
        </div>
      </div>

      {/* Right Side: Login Form */}
      <div className="w-full lg:w-2/5 flex items-center justify-center p-8 bg-dark-bg relative z-10 border-l border-white/5 shadow-[-20px_0_50px_rgba(0,0,0,0.5)]">
        <div className="w-full max-w-md space-y-10 animate-in fade-in slide-in-from-right duration-700 bg-white/[0.02] p-10 rounded-[2.5rem] border border-white/5 backdrop-blur-xl">
          <div className="lg:hidden text-center mb-10">
            <img src="/brand_icon_final.png" alt="FIT IQ" className="h-24 w-auto mx-auto drop-shadow-2xl mb-4 brightness-110" />
            <h1 className="text-3xl font-bold text-white tracking-widest">FIT IQ</h1>
          </div>

          <div className="space-y-4">
            <h2 className="text-4xl font-extrabold text-white tracking-tight">Login</h2>
            <p className="text-text-secondary text-lg">Seja bem-vindo ao futuro do treinamento.</p>
          </div>

          <form 
            onSubmit={(e) => {
              void handleSubmit(onSubmit)(e);
            }} 
            className="space-y-8"
          >
            <div className="space-y-4">
              <Input
                label="Endereço de Email"
                id="email"
                type="email"
                placeholder="nome@exemplo.com"
                leftIcon={<Mail size={20} className="text-text-muted" />}
                className="bg-white/5 border-white/10 h-14"
                error={errors.email?.message}
                {...register('email')}
              />

              <Input
                label="Senha"
                id="password"
                type="password"
                placeholder="Sua senha secreta"
                leftIcon={<Lock size={20} className="text-text-muted" />}
                className="bg-white/5 border-white/10 h-14"
                error={errors.password?.message}
                {...register('password')}
              />
            </div>

            <div className="flex items-center justify-end">
              <button
                type="button"
                className="text-sm font-semibold text-gradient-start hover:text-gradient-end transition-colors underline-offset-4 hover:underline"
              >
                Esqueceu a senha?
              </button>
            </div>

            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              className="h-14 text-xl font-bold bg-gradient-to-r from-gradient-start to-gradient-end shadow-orange hover:shadow-orange/40 transition-all rounded-xl"
            >
              Entrar na Plataforma
              {!isLoading && <LogIn className="ml-3" size={22} />}
            </Button>
            

          </form>
        </div>
      </div>
    </div>
  );
}
