import { useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { AppRoutes } from './AppRoutes';
import { useAuthStore } from './shared/hooks/useAuth';

/**
 * App component
 * 
 * Root component that initializes the application, 
 * sets up the router, and manages global state initialization.
 */
function App() {
  const init = useAuthStore((state) => state.init);

  useEffect(() => {
    // Load user info from token if it exists in localStorage
    void init();
  }, [init]);

  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
