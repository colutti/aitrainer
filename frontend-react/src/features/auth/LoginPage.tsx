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
    <div className="min-h-screen w-full flex bg-dark-bg">
      {/* Left side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 z-10">
        <div className="max-w-md w-full space-y-8 animate-in fade-in slide-in-from-left-8 duration-700">
          {/* Header */}
          <div className="text-center lg:text-left">
            <div className="inline-flex items-center gap-2 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-gradient-start to-gradient-end flex items-center justify-center font-bold text-white shadow-orange text-xl">
                F
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-gradient-start to-gradient-end bg-clip-text text-transparent">
                Fitiq
              </h1>
            </div>
            <h2 className="text-4xl font-black text-text-primary tracking-tight">
              Acesse sua conta
            </h2>
            <p className="text-text-secondary mt-2">
              Seu treinador pessoal de IA espera por você.
            </p>
          </div>

          {/* Form */}
          <form 
            onSubmit={(e) => {
              void handleSubmit(onSubmit)(e);
            }} 
            className="space-y-6"
          >
            <Input
              label="Email"
              id="email"
              type="email"
              placeholder="seu@email.com"
              leftIcon={<Mail size={18} />}
              error={errors.email?.message}
              {...register('email')}
            />

            <Input
              label="Senha"
              id="password"
              type="password"
              placeholder="••••••••"
              leftIcon={<Lock size={18} />}
              error={errors.password?.message}
              {...register('password')}
            />

            <div className="flex items-center justify-end">
              <button
                type="button"
                className="text-sm font-medium text-gradient-start hover:opacity-80 transition-opacity"
              >
                Esqueceu a senha?
              </button>
            </div>

            <Button
              type="submit"
              fullWidth
              isLoading={isLoading}
              className="text-lg font-bold py-6 rounded-xl"
            >
              Entrar
              {!isLoading && <LogIn className="ml-2" size={20} />}
            </Button>
          </form>

          {/* Footer */}
          <p className="text-center text-text-tertiary text-sm">
            Não tem uma conta?{' '}
            <button className="text-gradient-start font-bold hover:underline">
              Falar com o Treinador
            </button>
          </p>
        </div>
      </div>

      {/* Right side - Visual/Impact (Hidden on mobile) */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-dark-card border-l border-border">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-20 pointer-events-none">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--gradient-start)_0%,_transparent_70%)] opacity-30 blur-3xl" />
        </div>

        {/* Dynamic Image Overlay */}
        <div className="absolute inset-0 flex items-center justify-center p-12">
          <div className="relative group perspective-1000">
             <img 
               src="/assets/trainer-avatar.png" 
               alt="AI Trainer" 
               className="max-h-[80vh] w-auto drop-shadow-2xl animate-float transition-transform duration-500 group-hover:scale-105"
             />
             
             {/* Stats Cards / Floating Elements */}
             <div className="absolute top-1/4 -left-8 bg-dark-card/90 backdrop-blur-md border border-border p-4 rounded-2xl shadow-xl animate-float delay-75">
               <div className="flex items-center gap-3">
                 <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center text-green-500">
                    <LogIn size={20} />
                 </div>
                 <div>
                   <p className="text-xs text-text-tertiary uppercase font-bold tracking-wider">Status</p>
                   <p className="text-sm font-bold text-text-primary">Online</p>
                 </div>
               </div>
             </div>

             <div className="absolute bottom-1/4 -right-8 bg-dark-card/90 backdrop-blur-md border border-border p-4 rounded-2xl shadow-xl animate-float delay-150">
               <div className="flex items-center gap-3">
                 <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center text-orange-500">
                    <LogIn size={20} />
                 </div>
                 <div>
                   <p className="text-xs text-text-tertiary uppercase font-bold tracking-wider">Treinos</p>
                   <p className="text-sm font-bold text-text-primary">Pronto para começar</p>
                 </div>
               </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
