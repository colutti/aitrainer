import { Lock, Mail, Loader2, ShieldCheck, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAdminLogin, useAdminIsLoading, useAdminLoginError } from '../../shared/hooks/useAdminAuth';

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAdminLogin();
  const isLoading = useAdminIsLoading();
  const loginError = useAdminLoginError();
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [isHovered, setIsHovered] = useState(false);

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch {
      // Error is already set in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center overflow-hidden relative bg-[#050505]">
      {/* Dynamic Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-[#6366f1]/10 rounded-full blur-[120px] animate-pulse-glow" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-[#22d3ee]/10 rounded-full blur-[120px] animate-pulse-glow" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.03)_0%,transparent_70%)]" />
      </div>

      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      {/* Main Content Container */}
      <div className="relative z-10 w-full max-w-[440px] px-6 py-12">
        {/* Header Section */}
        <div className="text-center mb-12 animate-slide-in-fade">
          <div className="relative inline-block mb-8">
            <div className="absolute inset-0 bg-gradient-to-r from-[#6366f1] to-[#22d3ee] blur-2xl opacity-20 scale-150 animate-pulse" />
            <div className="relative bg-[#121214] p-4 rounded-2xl border border-white/10 shadow-2xl">
              <ShieldCheck className="h-10 w-10 text-[#6366f1]" />
            </div>
          </div>
          
          <h1 className="font-display text-4xl font-black tracking-tight mb-3">
            <span className="bg-gradient-to-r from-white via-white to-white/70 bg-clip-text text-transparent">FityQ </span>
            <span className="bg-gradient-to-r from-[#6366f1] to-[#22d3ee] bg-clip-text text-transparent">Admin</span>
          </h1>
          <p className="text-[#a1a1aa] text-base font-medium">Controle total da plataforma</p>
        </div>

        {/* Login Card with Glassmorphism */}
        <div 
          className="group relative bg-white/[0.02] backdrop-blur-xl border border-white/10 rounded-[32px] p-10 shadow-[0_0_50px_rgba(0,0,0,0.3)] overflow-hidden animate-slide-in-fade"
          style={{ animationDelay: '0.1s' }}
        >
          {/* Card Shine Effect */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

          {/* Error Message */}
          {loginError && (
            <div className="mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl animate-fade-in flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              <p className="text-sm font-medium text-red-400">
                {loginError === 'Access denied: admin role required'
                  ? 'Acesso negado: privilégios de admin requeridos'
                  : 'Credenciais inválidas. Tente novamente.'}
              </p>
            </div>
          )}

          <form
            onSubmit={(e) => {
              void handleSubmit(e);
            }}
            className="space-y-6"
          >
            {/* Email Field */}
            <div className="space-y-2">
              <label className="text-[13px] font-semibold text-[#71717a] ml-1 flex items-center gap-2">
                <Mail className="w-3.5 h-3.5" />
                ENDEREÇO DE EMAIL
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); }}
                required
                placeholder="admin@fityq.com"
                className="w-full px-5 py-4 bg-black/40 border border-white/5 rounded-2xl text-white placeholder-[#3f3f46] transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/30 focus:border-[#6366f1]/50 hover:bg-black/60 shadow-inner"
              />
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <label className="text-[13px] font-semibold text-[#71717a] ml-1 flex items-center gap-2">
                <Lock className="w-3.5 h-3.5" />
                SENHA DE ACESSO
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); }}
                required
                placeholder="••••••••"
                className="w-full px-5 py-4 bg-black/40 border border-white/5 rounded-2xl text-white placeholder-[#3f3f46] transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-[#6366f1]/30 focus:border-[#6366f1]/50 hover:bg-black/60 shadow-inner"
              />
            </div>

            {/* Action Button */}
            <button
              type="submit"
              disabled={isLoading}
              onMouseEnter={() => { setIsHovered(true); }}
              onMouseLeave={() => { setIsHovered(false); }}
              className="w-full mt-4 relative group/btn h-14 bg-gradient-to-r from-[#6366f1] to-[#22d3ee] rounded-2xl overflow-hidden transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100 disabled:cursor-not-allowed shadow-[0_10px_30px_rgba(99,102,241,0.3)]"
            >
              <div className="absolute inset-0 bg-white/10 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
              <div className="relative flex items-center justify-center gap-2 font-bold text-white tracking-wide">
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>VERIFICANDO...</span>
                  </>
                ) : (
                  <>
                    <span>ENTRAR NO PAINEL</span>
                    <ChevronRight className={`w-5 h-5 transition-transform duration-300 ${isHovered ? 'translate-x-1' : ''}`} />
                  </>
                )}
              </div>
            </button>
          </form>

          {/* Meta Information */}
          <div className="mt-10 pt-8 border-t border-white/5 flex flex-col items-center gap-4">
            <div className="px-3 py-1 bg-white/[0.03] border border-white/10 rounded-full flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[11px] font-bold text-[#a1a1aa] tracking-tight uppercase">Sistema Criptografado</span>
            </div>
            <p className="text-[11px] font-semibold text-[#52525b] uppercase tracking-widest">
              FityQ Administrative Core • v1.0
            </p>
          </div>
        </div>
        
        {/* Visual Decoration Footer */}
        <div className="mt-12 flex justify-center gap-12 animate-fade-in" style={{ animationDelay: '0.5s' }}>
           <div className="h-px w-12 bg-gradient-to-r from-transparent to-white/10" />
           <div className="text-[10px] text-[#3f3f46] font-bold tracking-widest uppercase">Secure Zone</div>
           <div className="h-px w-12 bg-gradient-to-l from-transparent to-white/10" />
        </div>
      </div>
    </div>
  );
}
