import { useEffect } from 'react';
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
  const { isAuthenticated, isLoading, logout } = useAuthStore();
  const location = useLocation();

  const isInviteLink = location.pathname === '/onboarding' && new URLSearchParams(location.search).has('token');

  useEffect(() => {
    if (isAuthenticated && isInviteLink) {
      logout();
    }
  }, [isAuthenticated, isInviteLink, logout]);

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    if (isInviteLink) {
      // Waiting for logout to complete
      return null;
    }
    // If user is already authenticated, redirect to dashboard or the page they was trying to access
    const state = location.state as { from?: { pathname: string } } | null;
    const from = state?.from?.pathname ?? '/dashboard';
    return <Navigate to={from} replace />;
  }

  return <>{children}</>;
}
