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
  const { isAuthenticated, userInfo, isLoading, logout } = useAuthStore();
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

    // Allow authenticated users to stay on onboarding if they haven't completed it
    if (location.pathname === '/onboarding' && userInfo && !userInfo.onboarding_completed) {
      return <>{children}</>;
    }

    // If user is already authenticated, redirect to dashboard or the page they was trying to access
    const state = location.state as { from?: { pathname: string; search?: string } } | null;
    const fromPath = state?.from?.pathname ?? '/dashboard';
    const fromSearch = state?.from?.search ?? '';
    return <Navigate to={`${fromPath}${fromSearch}`} replace />;
  }

  return <>{children}</>;
}
