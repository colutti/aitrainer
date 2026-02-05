import { Navigate, useLocation } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * AuthGuard component
 * 
 * Prevents authenticated users from accessing public-only routes (like /login).
 * Redirects to the home page (or intended destination) if already authenticated.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    // If user is already authenticated, redirect to home or the page they was trying to access
    const state = location.state as { from?: { pathname: string } } | null;
    const from = state?.from?.pathname ?? '/';
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}
