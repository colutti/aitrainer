import { useEffect, useRef } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { AppRoutes } from './AppRoutes';
import { ConfirmationProvider } from './shared/components/ui/ConfirmationProvider';
import { GlobalErrorBoundary } from './shared/components/ui/GlobalErrorBoundary';
import { ToastContainer } from './shared/components/ui/ToastContainer';
import { useAuthStore } from './shared/hooks/useAuth';

/**
 * App component
 * 
 * Root component that initializes the application, 
 * sets up the router, and manages global state initialization.
 */
function App() {
  const init = useAuthStore((state) => state.init);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const loadUserInfo = useAuthStore((state) => state.loadUserInfo);
  const lastFocusRefreshRef = useRef(0);

  useEffect(() => {
    // Load user info from token if it exists in localStorage
    void init();
  }, [init]);

  useEffect(() => {
    // Add window focus listener to refresh user info when user returns to app
    const handleFocus = () => {
      if (isAuthenticated) {
        const now = Date.now();
        if (now - lastFocusRefreshRef.current < 60_000) return;
        lastFocusRefreshRef.current = now;
        void loadUserInfo();
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => {
      window.removeEventListener('focus', handleFocus);
    };
  }, [isAuthenticated, loadUserInfo]);

  return (
    <BrowserRouter>
      <GlobalErrorBoundary>
        <AppRoutes />
        <ToastContainer />
        <ConfirmationProvider />
      </GlobalErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
