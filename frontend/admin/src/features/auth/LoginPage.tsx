import { Lock, Mail, Loader2 } from 'lucide-react';
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
    <div className="min-h-screen flex items-center justify-center overflow-hidden relative">
      {/* Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0a0b] via-[#1a1a2e] to-[#0a0a0b]">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-gradient-to-br from-[#6366f1]/20 to-transparent rounded-full blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-gradient-to-br from-[#22d3ee]/20 to-transparent rounded-full blur-3xl animate-pulse-glow" />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-md px-6">
        {/* Logo/Header */}
        <div className="text-center mb-10 animate-slide-in-fade">
          <div className="flex justify-center mb-6">
            <img
              src="/brand_icon_final.png"
              alt="FityQ"
              className="h-16 w-16 drop-shadow-[0_0_15px_rgba(99,102,241,0.4)]"
            />
          </div>
          <h1 className="font-display text-4xl font-black bg-gradient-to-r from-[#6366f1] to-[#22d3ee] bg-clip-text text-transparent mb-2">
            Painel Admin
          </h1>
          <p className="text-[#a1a1aa] text-sm font-medium">Acesso restrito</p>
        </div>

        {/* Card */}
        <div className="bg-[#121214] border border-white/8 rounded-2xl shadow-2xl p-8 animate-slide-in-fade"
             style={{ animationDelay: '0.1s' }}>

          {/* Error Message */}
          {loginError && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg animate-fade-in">
              <p className="text-sm font-medium text-red-400">
                {loginError === 'Access denied: admin role required'
                  ? 'Acesso negado: privilégios de admin requeridos'
                  : loginError}
              </p>
            </div>
          )}

          <form
            onSubmit={(e) => {
              handleSubmit(e).catch(() => {
                // Error is already set in store
              });
            }}
            className="space-y-5"
          >
            {/* Email Input */}
            <div>
              <label className="block text-xs font-semibold text-[#a1a1aa] uppercase tracking-wide mb-2">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6366f1]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); }}
                  required
                  placeholder="admin@example.com"
                  className="w-full pl-10 pr-4 py-3 bg-[#0a0a0b] border border-white/8 rounded-lg text-[#fafafa] placeholder-[#666666] transition-all focus:outline-none focus:border-[#6366f1]/50 focus:ring-1 focus:ring-[#6366f1]/30 hover:border-white/12"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label className="block text-xs font-semibold text-[#a1a1aa] uppercase tracking-wide mb-2">
                Senha
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6366f1]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); }}
                  required
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 bg-[#0a0a0b] border border-white/8 rounded-lg text-[#fafafa] placeholder-[#666666] transition-all focus:outline-none focus:border-[#6366f1]/50 focus:ring-1 focus:ring-[#6366f1]/30 hover:border-white/12"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-8 py-3 bg-gradient-to-r from-[#6366f1] to-[#22d3ee] text-white font-semibold rounded-lg transition-all duration-200 hover:shadow-[0_10px_25px_rgba(99,102,241,0.4)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Entrando...</span>
                </>
              ) : (
                'Entrar no Painel'
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-xs text-[#666666] mt-6">
            Acesso administrativo apenas • FityQ 2026
          </p>
        </div>
      </div>
    </div>
  );
}
