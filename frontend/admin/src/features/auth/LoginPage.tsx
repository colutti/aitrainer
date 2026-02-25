import { useAdminAuthStore } from '@shared/hooks/useAdminAuth';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';


export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, loginError } = useAdminAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleSubmit = async (e: any) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch {
      // Error is already set in store
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="w-full max-w-md p-8 bg-white rounded-lg shadow">
        <h1 className="text-2xl font-bold mb-6 text-center">Admin Portal</h1>

        {loginError && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            {loginError === 'Access denied: admin role required'
              ? 'Acesso negado: privilégios de admin requeridos'
              : loginError}
          </div>
        )}

        <form
          onSubmit={(e) => {
            handleSubmit(e).catch(console.error);
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); }}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); }}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
}
