import { Navigate, useLocation } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

/**
 * ProtectedRoute component
 * 
 * Guards routes that require authentication.
 * Redirects to /login if not authenticated.
 * Redirects to / if authenticated but lacks admin privileges (when required).
 */
export function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const { isAuthenticated, isAdmin, isLoading } = useAuthStore();
  const location = useLocation();

  if (isLoading) {
    return null; // Or a loading spinner/skeleton
  }

  if (!isAuthenticated) {
    // Redirect to login but save the current location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !isAdmin) {
    // If admin is required but user is not admin, redirect to dashboard/home
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
