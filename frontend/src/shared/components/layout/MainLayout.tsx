import { Outlet } from 'react-router-dom';

import { useInactivityLogout } from '../../hooks/useInactivityLogout';
import { useTokenRefresh } from '../../hooks/useTokenRefresh';
import { ConfirmationProvider } from '../ui/ConfirmationProvider';
import { ToastContainer } from '../ui/ToastContainer';

import { BottomNav } from './BottomNav';
import { Sidebar } from './Sidebar';

/**
 * MainLayout component
 *
 * Provides the core shell for the application, including:
 * - Desktop Sidebar
 * - Mobile Bottom Navigation
 * - Global notification system (Toasts)
 * - Global confirmation modals
 * - Automatic logout on inactivity
 * - Main content area via Router <Outlet />
 */
export function MainLayout() {
  useInactivityLogout();
  useTokenRefresh();

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary flex">
      {/* Platform Utilities */}
      <ToastContainer />
      <ConfirmationProvider />

      {/* Navigation - Desktop */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col lg:pl-64 pb-16 md:pb-20 lg:pb-0 min-h-screen transition-all duration-300 overflow-x-hidden">
        <div className="flex-1 max-w-7xl mx-auto w-full p-4 md:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Navigation - Mobile */}
      <BottomNav />
    </div>
  );
}
